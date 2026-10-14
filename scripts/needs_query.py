#!/usr/bin/env python3
"""need.json 問い合わせのコアロジック - 要件の取得・検索・トレース・集計。

sphinx-needs がビルド時に出力する needs.json（ADR-0004）を読み、
AI やスクリプトが扱いやすい小さな辞書に整形して返す。

このモジュールは MCP に依存しない。MCP サーバー（needs_mcp_server.py）は
この上の薄い殻であり、同じ関数はテストや CI からも直接呼べる。

使用例：
    store = load_needs(Path("_build/html/needs.json"))
    trace(store, "SYS_001", direction="down")
"""
from __future__ import annotations

import dataclasses
import difflib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Literal

# -----------------------------------------------------------------------------
# 定数
# -----------------------------------------------------------------------------

#: needs.json の既定パス（リポジトリルートからの相対。docs/_build ではない）
DEFAULT_NEEDS_JSON: str = "_build/html/needs.json"

#: 一覧で返すフィールド。トークンを節約するため最小限にする。
SUMMARY_FIELDS: tuple[str, ...] = ("id", "type", "title", "status")

#: 詳細で返すフィールド。1件 約70項目のうち、sphinx-needs 内部用を除いたもの。
DETAIL_FIELDS: tuple[str, ...] = (
    "id", "type", "title", "status",
    "type_kind", "layer", "method", "environment",
    "tbd_items", "open_params", "rationale", "content",
)

#: 上流へ辿るリンク（この need が指している先）。conf.py の needs_links と対応。
UPSTREAM_LINKS: tuple[str, ...] = ("refines", "verifies")

#: 下流へ辿るリンク（この need を指しているもの）。sphinx-needs が生成する逆リンク。
DOWNSTREAM_LINKS: tuple[str, ...] = ("refines_back", "verifies_back")

#: 原稿の拡張子（このプロジェクトの原稿は全て MyST Markdown）
SOURCE_SUFFIX: str = ".md"

#: 鮮度チェックの対象。これが needs.json より新しければ再ビルドが必要。
WATCHED_SUFFIXES: frozenset[str] = frozenset({".md", ".py"})

Direction = Literal["up", "down", "both"]

# -----------------------------------------------------------------------------
# データ
# -----------------------------------------------------------------------------

@dataclasses.dataclass(frozen=True)
class NeedsStore:
    """読み込んだ needs.json の中身。

    Attributes:
        needs: need ID → need 辞書（sphinx-needs の生データ）。
        built_at: needs.json の出力日時（ファイル内の created）。
        stale_sources: needs.json より新しい原稿の一覧。空なら最新。
    """
    needs: dict[str, dict[str, Any]]
    built_at: str
    stale_sources: tuple[str, ...] = ()

class NeedNotFoundError(LookupError):
    """指定した ID の need が needs.json に存在しない。"""

# -----------------------------------------------------------------------------
# 読み込み
# -----------------------------------------------------------------------------
def load_needs(path: Path, docs_dir: Path | None = None) -> NeedsStore:
    """needs.json を読み込む。

    sphinx-needs の標準形式（versions 配下）から現在の版を取り出す。
    版の選び方は metadata_lint.py の load_needs_ids と揃えている。

    Args:
        path: needs.json のパス。
        docs_dir: 原稿のディレクトリ。指定すると鮮度チェックを行う。

    Returns:
        読み込んだ内容。

    Raises:
        FileNotFoundError: needs.json がない（make rebuild 前など）。
    """
    if not path.is_file():
        raise FileNotFoundError(
            f"needs.json がありません: {path} （make rebuild で生成されます）"
        )
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    versions: dict[str, Any] = data["versions"]
    current: str | None = data.get("current_version")
    key: str = (
        current if current is not None and current in versions
        else sorted(versions)[-1]
    )
    stale: tuple[str, ...] = ()
    if docs_dir is not None:
        stale = find_newer_sources(path, docs_dir)
    return NeedsStore(
        needs=versions[key]["needs"],
        built_at=str(data.get("created", "")),
        stale_sources=stale,
    )

def find_newer_sources(
        needs_json: Path, docs_dir: Path, limit: int = 5
) -> tuple[str, ...]:
    """needs.json より後に更新された原稿を探す。

    Args:
        needs_json: needs.json のパス。
        docs_dir: 原稿のディレクトリ。
        limit: 返す件数の上限。

    Returns:
        needs.json より新しいファイル（docs_dir からの相対パス）。
    """
    built: float = needs_json.stat().st_mtime
    newer: list[str] = sorted(
        str(p.relative_to(docs_dir))
        for p in docs_dir.rglob("*")
        if p.suffix in WATCHED_SUFFIXES and p.stat().st_mtime > built
    )
    return tuple(newer[:limit])

# -----------------------------------------------------------------------------
# 問い合わせ
# -----------------------------------------------------------------------------

def get_need(store: NeedsStore, need_id: str) -> dict[str, Any]:
    """need 1 件の詳細を返す。

    Args:
        store: 読み込んだ needs.json。
        need_id: need の ID（例: "SWR_012"）。

    Returns:
        DETAIL_FIELDS に絞った辞書に、上流・下流のリンク（upstream /
        downstream）と原稿の位置（source）を加えたもの。

    Raises:
        NeedNotFoundError: ID が存在しない。
    """
    need: dict[str, Any] = _require(store, need_id) 
    detail: dict[str, Any] = _pick(need, DETAIL_FIELDS)
    detail["upstream"] = {f: need[f] for f in UPSTREAM_LINKS if need.get(f)}
    detail["downstream"] = {f: need[f] for f in DOWNSTREAM_LINKS if need.get(f)}
    detail["source"] = f"docs/{need['docname']}{SOURCE_SUFFIX}:{need['lineno']}"
    return detail

def search_needs(
        store: NeedsStore,
        need_type: str | None = None,
        status: str | None = None,
        environment: str | None = None,
        text: str | None = None,
        limit: int = 50,
) -> dict[str, Any]:
    """条件に合う need の一覧を ID 順に返す。
    
    Args:
        store: 読み込んだ needs.json。
        need_type: タイプで絞る（sysreq / arc / swreq / swverif）。
        status: ステータスで絞る（draft / approved / obsolete）。
        environment: 検証環境で絞る（host / target / ci / review）。
        text: ID・タイトル・本文の部分一致（大文字小文字を区別しない）。
        limit: 返す件数の上限。

    Returns:
        count（該当件数）、needs（SUMMARY_FIELDS の一覧）、truncated（上限で切ったか）。
    """
    keyword: str | None = text.lower() if text else None
    hits: list[dict[str, Any]] = []
    for need_id in sorted(store.needs):
        need: dict[str, Any] = store.needs[need_id]
        if need_type and need.get("type") != need_type:
            continue
        if status and need.get("status") != status:
            continue
        if environment and need.get("environment") != environment:
            continue
        if keyword and keyword not in _haystack(need):
            continue
        hits.append(_pick(need, SUMMARY_FIELDS))
    return {"count": len(hits), "needs": hits[:limit], "truncated": len(hits)>limit}

def trace(
        store: NeedsStore,
        need_id: str,
        direction: Direction = "both",
        max_depth: int = 3,
) -> dict[str, Any]:
    """リンクを辿って、上流・下流の need を列挙する。
    
    上流 = この need が refines / verifies している先（SWV → SWR → SYS）。
    下流 = この need を refines / verifies しているもの（SYS → SWR → SWV）。

    Args:
        store: 読み込んだ needs.json。
        need_id: 起点の ID。
        direction: "up"（上流） / "down"（下流） / "both"（両方）。
        max_depth: 辿る段数の上限。

    Returns:
        root（起点の要約）と upstream / downstream の一覧。各要素は要約に
        via（辿ったリンク）・from（辿る元）・depth（段数）を加えたもの。

    Raises:
        NeedNotFoundError: ID が存在しない。
    """
    root: dict[str, Any] = _require(store, need_id)
    result: dict[str, Any] = {"root": _pick(root, SUMMARY_FIELDS)}
    if direction in ("up", "both"):
        result["upstream"] = _walk(store, root["id"], UPSTREAM_LINKS, max_depth)
    if direction in ("down", "both"):
        result["downstream"] = _walk(store, root["id"], DOWNSTREAM_LINKS, max_depth)
    return result

def status_report(store: NeedsStore) -> dict[str, Any]:
    """要件・検証ケース全体の状況をまとめる。
    
    ビルド時のゲート（conf.py の needs_warnings）は承認済みの要件しか見ない。
    ここでは draft も含めて、承認前に手当てが必要なものを先回りで拾う。
    
    Args:
        store: 読み込んだ needs.json。

    Returns:
        built_at（出力日時）、counts（タイプ別・ステータス別の件数）、
        swreq_without_verification（検証ケースのない SWR、obsolete を除く）、
        tbd_items（構造的 TBD の ID → 内容）、open_params（パラメータ TBD を持つ ID）、
        swverif_by_environment（検証ケースの環境別件数）。
    """
    ordered: list[dict[str, Any]] = [store.needs[k] for k in sorted(store.needs)]
    counts: dict[str, dict[str, int]] = {}
    for need in ordered:
        by_status: dict[str, int] = counts.setdefault(need["type"], {})
        status: str = need.get("status") or "unset"
        by_status[status] = by_status.get(status, 0) + 1
    return {
        "built_at": store.built_at,
        "counts": counts,
        "swreq_without_verification": [
            n["id"] for n in ordered
            if n["type"] == "swreq"
            and n.get("status") != "obsolete"
            and not n.get("verifies_back")
        ],
        "tbd_items": {n["id"]: n["tbd_items"] for n in ordered if n.get("tbd_items")},
        "open_params": [n["id"] for n in ordered if n.get("open_params")],
        "swverif_by_environment": dict(Counter(
            n.get("environment") or "unset" for n in ordered if n["type"] == "swverif"
        )),
    }

# -----------------------------------------------------------------------------
# 内部ヘルパー
# -----------------------------------------------------------------------------

def _require(store: NeedsStore, need_id: str) -> dict[str, Any]:
    """ID で need を引く。なければ近い ID を添えて例外にする。"""
    key: str = need_id.strip().upper()
    need: dict[str, Any] | None = store.needs.get(key)
    if need is None:
        close: list[str] = difflib.get_close_matches(key, store.needs, n=3, cutoff=0.6)
        hint: str = f"近い ID: {', '.join(close)}" if close else "ID の綴りを確認してください"
        raise NeedNotFoundError(f"{need_id} は needs.json に存在しません。{hint}")
    return need

def _pick(need: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    """指定したフィールドだけを取り出す。空の値（None・空文字・空リスト）は省く。"""
    return {f: need[f] for f in fields if need.get(f) not in (None, "", [])}

def _haystack(need: dict[str, Any]) -> str:
    """部分一致検索の対象文字列（ID・タイトル・本文）を作る。"""
    return " ".join(str(need.get(f) or "") for f in ("id", "title", "content")).lower()

def _walk(
        store: NeedsStore, start: str, links: tuple[str, ...], max_depth: int
) -> list[dict[str, Any]]:
    """幅優先でリンクを辿る。同じ need は一度だけ数える（循環対策）。"""
    seen: set[str] = {start}
    frontier: list[str] = [start]
    found: list[dict[str, Any]] = []
    for depth in range(1, max_depth + 1):
        next_frontier: list[str] = []
        for current in frontier:
            for link in links:
                for target in store.needs[current].get(link) or []:
                    if target in seen or target not in store.needs:
                        continue
                    seen.add(target)
                    next_frontier.append(target)
                    found.append({
                        **_pick(store.needs[target], SUMMARY_FIELDS),
                        "via": link,
                        "from": current,
                        "depth": depth,
                    })
        frontier = next_frontier
    return found
