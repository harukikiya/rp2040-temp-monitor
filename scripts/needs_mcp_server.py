#!/usr/bin/env python3
"""needs.json 問い合わせ MCP サーバー - Claude Code から要件・検証ケースを引く。

needs_query.py の関数を MCP のツールとして公開するだけの薄い層。
ツールは全て読み取り専用で、ファイルを書き換えない。

注意：stdio トランスポートでは標準出力が JSON-RPC 専用の通り道になる。
print() で標準出力に書くとプロトコルが壊れるため、ログは標準エラー出力に出す。

使用例：
    uv run python scripts/needs_mcp_server.py
    uv run python sctipts/needs_mcp_server.py --needs-json tests/fixtures/needs_mini.json

通常は .mcp.json の設定に従って Claude Code が起動する。
"""
from __future__ import annotations

import argparse
import contextlib
import logging
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Literal

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

import needs_query as nq

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

#: リポジトリルート（このファイルは scripts/ 直下にある）
REPO_ROOT: Path = Path(__file__).resolve().parent.parent

#: 4 ツール共通の注釈。読み取り専用・何度呼んでも同じ結果・外部と通信しない。
READ_ONLY: ToolAnnotations = ToolAnnotations(
    read_only_hint=True, idempotent_hint=True, open_world_hint=False
)

#: 接続時にクライアントへ渡す使い方の説明（モデルがツールを選ぶ手掛かりになる）
INSTRUCTIONS: str = (
    "rp2040-temp-monitor の要件（SYS/ARC/SWR）と検証ケース（SWV）を、"
    "sphinx-needs が出力した needs.json から引く。"
    "ID が分かれば get_need、分からなければ search_needs、"
    "変更の影響範囲は trace、全体の状況は status_report を使う。"
)

NeedType = Literal["sysreq", "arc", "swreq", "swverif"]
Status = Literal["draft", "approved", "obsolete"]
Environment = Literal["host", "target", "ci", "review"]
Direction = Literal["up", "down", "both"]

log: logging.Logger = logging.getLogger("needs-mcp")

# ---------------------------------------------------------------------------
# サーバー
# ---------------------------------------------------------------------------

def build_server(needs_json: Path, docs_dir: Path | None = None) -> MCPServer:
    """ 4 つのツールを登録した MCP サーバーを作る。

    パスを引数で受け取るのは、テストで小さな fixture を読ませるため。

    Args:
        needs_json: 読み込む needs.json のパス。
        docs_dir: 原稿のディレクトリ。指定すると鮮度チェックを行う。

    Returns:
        ツールを登録したサーバー。
    """
    server = MCPServer(name="rp2040-needs", instructions=INSTRUCTIONS)

    def load() -> nq.NeedsStore:
        # 呼ばれるたびに読み直す。97 件で数ミリ秒なので、キャッシュは持たない。
        return nq.load_needs(needs_json, docs_dir)

    @server.tool(annotations=READ_ONLY)
    def get_need(need_id: str) -> dict[str, Any]:
        """要件・検証ケース 1 件の詳細を返す。
        
        本文、フィールド、上流・下流のリンク、原稿の位置（source）を含む。
        ID が分かっているときに使う。分からないときは search_needs を使う。

        Args:
            need_id: need の ID（例："SWR_012"、"SWV_003"）。
        """
        with _as_tool_error():
            store = load()
            return _with_freshness(store, nq.get_need(store, need_id))

    @server.tool(annotations=READ_ONLY)
    def search_needs(
        need_type: NeedType | None = None,
        status: Status | None = None,
        environment: Environment | None = None,
        text: str | None = None,
    ) -> dict[str, Any]:
        """条件に合う要件・検証ケースの一覧（ID・タイトル・ステータス）を返す。
        
        本文は返さない。気になった ID は get_need で詳細を見る。

        Args:
            need_type: sysreq（システム要件） / arc（アーキテクチャ要件） /
                        swreq（ソフトウェア要件） / swverif（検証ケース）。
            status: draft / approved / obsolete。
            environment: 検証環境（host / target / ci / review）。swverif 向け。
            text: ID・タイトル・本文の部分一致。
        """
        with _as_tool_error():
            store = load()
            result = nq.search_needs(
                store, need_type=need_type, status=status,
                environment=environment, text=text,
            )
            return _with_freshness(store, result)

    @server.tool(annotations=READ_ONLY)
    def trace(need_id: str, direction: Direction = "both") -> dict[str, Any]:
        """refines / verifies のリンクを辿り、上流・下流の need を列挙する。
        
        変更の影響範囲（この SYS を変えたらどの SWR・SWV に波及するか）は
        direction = "down"、要件の出どころを確かめるときは "up" を使う。

        Args:
            need_id: 起点の ID。
            direction: "up"（上流） / "down"（下流） / "both"（両方）。
        """
        with _as_tool_error():
            store = load()
            return _with_freshness(store, nq.trace(store, need_id, direction))

    @server.tool(annotations=READ_ONLY)
    def status_report() -> dict[str, Any]:
        """要件・検証ケース全体の状況を返す。
        
        タイプ別・ステータス別の件数、検証ケースのない SWR、
        構造的 TBD（tbd_items）とパラメータ TBD（open_params）を持つ need、
        検証ケースの環境別件数を含む。
        """
        with _as_tool_error():
            store = load()
            return _with_freshness(store, nq.status_report(store))

    return server

@contextlib.contextmanager
def _as_tool_error() -> Iterator[None]:
    """コアの「想定内の失敗」を ToolError に変換して、メッセージをモデルに届ける。
    
    ToolError 以外の例外は SDK がクラッシュとして扱い、モデルには
    「Error executing tool <名前>」しか見せない（内部情報を漏らさないため）。
    """
    try:
        yield
    except (nq.NeedNotFoundError, FileNotFoundError) as exc:
        raise ToolError(str(exc)) from exc

def _with_freshness(store: nq.NeedsStore, result: dict[str, Any]) -> dict[str, Any]:
    """原稿が needs.json より新しければ、結果に警告を添える。"""
    if store.stale_sources:
        result["warning"] = (
            "needs.json より新しい原稿があります（"
            + ", ".join(store.stale_sources)
            + "）。make rebuild してから問い合わせ直してください。"
        )
    return result

# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------
def main() -> None:
    """コマンドライン引数を読み、stdio でサーバーを起動する。"""
    parser = argparse.ArgumentParser(description="needs.json 問い合わせ MCP サーバー")
    parser.add_argument(
        "--needs-json", type=Path, default=REPO_ROOT / nq.DEFAULT_NEEDS_JSON,
        help="読み込む needs.json（既定: _build/html/needs.json）",
    )
    parser.add_argument(
        "--docs-dir", type=Path, default=REPO_ROOT / "docs",
        help="鮮度チェックに使う原稿のディレクトリ（既定: docs/）",
    )
    args = parser.parse_args()

    # 標準出力は JSON-RPC 専用。ログは必ず標準エラー出力へ。
    logging.basicConfig(
        stream=sys.stderr, level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    log.info("needs.json: %s", args.needs_json)
    build_server(args.needs_json, args.docs_dir).run()      # 既定のトランスポートは stdio

if __name__ == "__main__":
    main()
