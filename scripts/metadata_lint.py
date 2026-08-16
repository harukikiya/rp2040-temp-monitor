#!/usr/bin/env python3
"""メタデータ linter - frontmatter・トレースタグ・ID 参照の機械検証。

メタデータ方針の原則 P4 「検証されないメタデータは腐る」を実行するツール。
以下を検査し、CI ゲートとして使えるよう終了コードを結果で返す。

検査項目：
    [MD] Markdown frontmatter
        MD01：frontmatter の存在（設定で必須化した場合）
        MD02：YAML として妥当か
        MD03：必須フィールドの存在（type ほか、設定で定義）
        MD04：列挙値の妥当性（type / aspice など、設定で定義）
        MD05：禁止フィールドの不在（timestamp / status / author など = P1/二重管理防止）
        MD06：未知キー（警告 - OKF は未知キー許容を求めるため error にしない）
        MD07：relates[] の参照実在性（needs.json の ID / ADR ファイル）
        MD08：本文中に書かれた要件 ID の実在性（壊れた参照の検出）
    [SRC] ソースコード
        SRC01：@satisfies タグの参照 ID が needs.json に実在するか
    [XR] 横断
        XR01：どのソースからも @satisfies されていない要件（情報レベル）

終了コード：
    0 = エラーなし（警告は許容。 --strict なら警告もエラー扱い）
    1 = エラーあり
    2 = 設定・入力の不備

使用例：
    python3 metadata_lint.py --config metadata.yaml
    python3 metadata_lint.py --config metadata.yaml --format json
    python3 metadata_lint.py --config metadata.yaml --strict
"""
from __future__ import annotations

import argparse
import dataclasses
import glob
import json
import os
import re
import sys
from typing import Any, Optional

import yaml

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

SEVERITY_ERROR: str = "error"
SEVERITY_WARNING: str = "warning"
SEVERITY_INFO: str = "info"

FRONTMATTER_DELIM: str = "---"

# @satisfies SWR_001 / @satisfies{SWR_001} の両形式を許容する
SATISFIES_RE: re.Pattern[str] = re.compile(
    r"@satisfies\s*\{?\s*([A-Z][A-Z0-9]*_[0-9]+)\s*\}?"
)

# relates での参照形式：要件 ID（SWR_001 等）と ADR 番号（ADR-0003）
NEED_ID_RE: re.Pattern[str] = re.compile(r"^[A-Z][A-Z0-9]*_[0-9]+$")

# 本文中に現れる要件 ID らしき文字列（SYS_001 / ARC_002 / SWR_040 など）
BODY_ID_RE: re.Pattern[str] = re.compile(r"\b([A-Z][A-Z0-9]*_[0-9]{3,})\b")
ADR_ID_RE: re.Pattern[str] = re.compile(r"^ADR-([0-9]{4})$")

# ---------------------------------------------------------------------------
# データ型
# ---------------------------------------------------------------------------
@dataclasses.dataclass
class Finding:
    """1件の検出結果。

    Attributes:
        rule: 検査項目の ID（例："MD03"）。
        severity: 深刻度（error / warning / info）。
        path: 対象ファイルのパス。
        message: 人間向けの説明。
        line: 該当行番号（特定できる場合のみ）。
    """
    rule: str
    severity: str
    path: str
    message: str
    line: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        """JSON 出力用の辞書に変換する。
        
        Returns:
            フィールド名をキーとする辞書。line が None の場合は含めない。
        """
        d: dict[str, Any] =  {
            "rule": self.rule,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
        }
        if self.line is not None:
            d["line"] = self.line
        return d

@dataclasses.dataclass
class Config:
    """linter の設定（YAML から読み込む）。
    
    Attributes:
        docs_globs: 検査対象 Markdown の glob パターン一覧。
        docs_exclude: 除外する glob パターン一覧。
        src_globs: @satisfies を走査するソースの glob パターン一覧。
        needs_json: sphinx-needs がエクスポートした needs.json のパス。
        adr_dir: ADR ファイルのディレクトリ（ADR-#### の実在確認に使う）。
        frontmatter_required: True なら frontmatter 不在を警告する。
        required_fields: 全文書で必須のフィールド名一覧。
        enums: フィールド名 → 許容値一覧。
        forbidden_fields: フィールド名 → 禁止理由（P1 / 二重管理防止）。
        known_fields: 既知フィールドの一覧（これ以外は MD06 警告）。
        report_unsatisfied_needs: True なら XR01（未実装要件）を情報として出す。
        check_body_ids: True なら MD08（本文中の ID 参照の実在性）を検査する。
        body_id_ignore: MD08 で無視する ID の一覧（欠番の説明文など、実在しないことを承知で言及している ID）。
    """
    docs_globs: list[str]
    docs_exclude: list[str]
    src_globs: list[str]
    needs_json: Optional[str]
    adr_dir: Optional[str]
    frontmatter_required: bool
    required_fields: list[str]
    enums: dict[str, list[str]]
    forbidden_fields: dict[str, str]
    known_fields: list[str]
    report_unsatisfied_needs: bool
    check_body_ids: bool
    body_id_ignore: list[str]

# ---------------------------------------------------------------------------
# 読み込み
# ---------------------------------------------------------------------------
def load_config(path: str) -> Config:
    """設定 YAML を読み込み Config に詰める。

    Args:
        path: 設定ファイルのパス。

    Returns:
        検証済みの Config。

    Raises:
        SystemExit: ファイルが無い・YAML が壊れている場合（終了コード 2）。
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw: dict[str, Any] = yaml.safe_load(f) or {}
    except FileNotFoundError:
        sys.exit(f"設定ファイルが見つかりません: {path}")
    except yaml.YAMLError as e:
        print(f"設定 YAML の解析に失敗: {e}", file=sys.stderr)
        sys.exit(2)

    return Config(
        docs_globs=list(raw.get("docs_globs", [])),
        docs_exclude=list(raw.get("docs_exclude", [])),
        src_globs=list(raw.get("src_globs", [])),
        needs_json=raw.get("needs_json"),
        adr_dir=raw.get("adr_dir"),
        frontmatter_required=bool(raw.get("frontmatter_required", False)),
        required_fields=list(raw.get("required_fields", ["type"])),
        enums={k: list(v) for k, v in (raw.get("enums") or {}).items()},
        forbidden_fields=dict(raw.get("forbidden_fields") or {}),
        known_fields=list(raw.get("known_fields", [])),
        report_unsatisfied_needs=bool(raw.get("report_unsatisfied_needs", True)),
        check_body_ids=bool(raw.get("check_body_ids", False)),
        body_id_ignore=list(raw.get("body_id_ignore", [])),
    )

def load_needs_ids(path: Optional[str]) -> Optional[set[str]]:
    """needs.json から need ID の集合を取り出す。
    
    sphinx-needs の標準形式（versions 配下）と、単純な {"needs": {...}}
    の両方に対応する。

    Args:
        path: needs.json のパス。None なら ID 検査をスキップする。

    Returns:
        ID の集合。path が None なら None（= 検査スキップの意味）。

    Raises:
        SystemExit: ファイルがない・JSON が壊れている場合（終了コード 2）。
    """
    if path is None:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
    except FileNotFoundError:
        sys.exit(f"needs.json が見つかりません: {path}")
    except json.JSONDecodeError as e:
        print(f"needs.json の解析に失敗: {e}", file=sys.stderr)
        sys.exit(2)

    needs: dict[str, Any] = {}
    if "versions" in data:
        versions: dict[str, Any] = data["versions"]
        current: Optional[str] = data.get("current_version")
        key: str = current if current in versions else sorted(versions)[-1]
        needs = versions[key].get("needs", {})
    else:
        needs = data.get("needs", {})
    return set(needs.keys())

def collect_files(globs: list[str], excludes: list[str]) -> list[str]:
    """glob パターン群からファイル一覧を集め、除外を適用する。

    Args:
        globs: 収集する glob パターン。
        excludes: 除外する glob パターン。

    Returns:
        ソート済みのファイルパス一覧（重複除去済み）。
    """
    found: set[str] = set()
    for pat in globs:
        found.update(p for p in glob.glob(pat, recursive=True) if os.path.isfile(p))
    excluded: set[str] = set()
    for pat in excludes:
        excluded.update(glob.glob(pat, recursive=True))
    return sorted(found - excluded)

# ---------------------------------------------------------------------------
# frontmatter の抽出と検査
# ---------------------------------------------------------------------------

def extract_frontmatter(text: str) -> "tuple[Optional[dict[str, Any]], Optional[str]]":
    """Markdown テキストから frontmatter を抽出する。
    
    先頭行が '---' で始まり、次に単独行 '---' が現れるまでを YAML として解釈する。

    Args:
        text: ファイル全文。

    Returns:
        (frontmatter辞書, エラーメッセージ) のタプル。
        frontmatter がない場合は (None, None) 。
        YAML が壊れている場合は (None, エラーメッセージ) 。
    """
    lines: list[str] = text.splitlines()
    if not lines or lines[0].strip() != FRONTMATTER_DELIM:
        return None, None
    for i in range(1, len(lines)):
        if lines[i].strip() == FRONTMATTER_DELIM:
            block: str = "\n".join(lines[1:i])
            try:
                parsed: Any = yaml.safe_load(block)
            except yaml.YAMLError as e:
                return None, f"YAML 解析エラー: {e}"
            if parsed is None:
                return {}, None
            if not isinstance(parsed, dict):
                return None, "frontmatter がマッピング（key: value）ではありません"
            return parsed, None
    return None, "frontmatter の閉じ '---' が見つかりません"

def check_markdown(
        path: str,
        cfg: Config,
        need_ids: Optional[set[str]],
) -> list[Finding]:
    """1つの Markdown ファイルの frontmatter を検査する。

    Args:
        path: 対象ファイル。
        cfg: linter 設定。
        need_ids: needs.json 由来の ID 集合（None なら参照検査をスキップ）。

    Returns:
        検出結果の一覧。
    """
    findings: list[Finding] = []
    with open(path, "r", encoding="utf-8") as f:
        text: str = f.read()

    # MD08 は frontmatter の有無と無関係なので、先に実行する
    findings.extend(check_body_ids(path, text, cfg, need_ids))

    fm: Optional[dict[str, Any]]
    err: Optional[str]
    fm, err = extract_frontmatter(text)

    if err is not None:
        findings.append(Finding("MD02", SEVERITY_ERROR, path, err, line=1))
        return findings
    if fm is None:
        if cfg.frontmatter_required:
            findings.append(Finding(
                "MD01", SEVERITY_WARNING, path,
                "frontmatter がありません（導入対象の文書です）", line=1))
        return findings

    # MD03: 必須フィールド
    for field in cfg.required_fields:
        if field not in fm:
            findings.append(Finding(
                "MD03", SEVERITY_ERROR, path,
                f"必須フィールド '{field}' がありません"))

    # MD04: 列挙値
    for field, allowed in cfg.enums.items():
        if field in fm and fm[field] not in allowed:
            findings.append(Finding(
                "MD04", SEVERITY_ERROR, path,
                f"'{field}: {fm[field]}' は許容値 {allowed} にありません"))

    # MD05: 禁止フィールド（P1 / 二重管理防止）
    for field, reason in cfg.forbidden_fields.items():
        if field in fm and fm[field] not in allowed:
            findings.append(Finding(
                "MD05", SEVERITY_ERROR, path,
                f"禁止フィールド '{field}' が書かれています（{reason}）"))

    # MD06: 未知キー（OKF の未知キー許容原則により warning 止まり）
    if cfg.known_fields:
        known: set[str] = set(cfg.known_fields) | set(cfg.forbidden_fields)
        for field in fm:
            if field not in known:
                findings.append(Finding(
                    "MD06", SEVERITY_WARNING, path,
                    f"未知のフィールド '{field}' （スキーマへの追加は消費者の明記が条件 = P2）"))

    # MD07: relates の参照実在性
    relates: Any = fm.get("relates", [])
    if relates and not isinstance(relates, list):
        findings.append(Finding(
            "MD07", SEVERITY_ERROR, path,
            f"'relates' はリストで書いてください（現在： {type(relates).__name__}）"))
        relates = []
    for ref in relates or []:
        ref_s: str = str(ref)
        if NEED_ID_RE.match(ref_s):
            if need_ids is not None and ref_s not in need_ids:
                findings.append(Finding(
                    "MD07", SEVERITY_ERROR, path,
                    f"relates の '{ref_s}' が needs.json に存在しません"))
        elif ADR_ID_RE.match(ref_s):
            if cfg.adr_dir is not None:
                num: str = ADR_ID_RE.match(ref_s).group(1) # type: ignore[union-attr]
                hits: list[str] = glob.glob(os.path.join(cfg.adr_dir, f"{num}-*.md"))
                if not hits:
                    findings.append(Finding(
                        "MD07", SEVERITY_ERROR, path,
                        f"relates の '{ref_s}' に対応する ADR ファイルが "
                        f"{cfg.adr_dir} にありません"))

        else:
            findings.append(Finding(
                "MD07", SEVERITY_WARNING, path,
                f"relates の '{ref_s}' は既知の ID 形式"
                "（SWR_001 / SYS_001 / ADR-0001 等）ではありません"))

    return findings

def check_body_ids(
        path: str,
        text: str,
        cfg: Config,
        need_ids: Optional[set[str]],
) -> list[Finding]:
    """本文中に書かれた要件 ID が needs.json に実在するかを検査する。

    ADR や設計書の説明文から要件を参照するとき、ID 書き間違えても
    Sphinx はエラーにしない（単なる文字列のため）。
    壊れた参照はトレーサビリティの穴になるので、機械的に検出する。

    need 定義そのものの ``:id:`` 行は対象外にする。また、欠番を説明する
    文のように「実在しないことを承知で言及している」ID は設定で除外できる。

    Args:
        path: 対象ファイル。
        text: ファイル全文。
        cfg: linter 設定。
        need_ids: needs.json 由来の ID 集合（None なら検査しない）。

    Returns:
        検出結果の一覧。
    """
    if (not cfg.check_body_ids) or (need_ids is None):
        return []

    findings: list[Finding] = []
    ignore: set[str] = set(cfg.body_id_ignore)
    reported: set[str] = set()

    for lineno, line in enumerate(text.splitlines(), start=1):
        # need 定義の :id: 行は定義側なので対象外
        if line.lstrip().startswith(":id:"):
            continue
        for m in BODY_ID_RE.finditer(line):
            ref: str = m.group(1)
            if (ref in need_ids) or (ref in ignore) or (ref in reported):
                continue
            reported.add(ref)
            findings.append(Finding(
                "MD08", SEVERITY_ERROR, path,
                f"本文中の '{ref}' が needs.json に存在しません"
                "（誤記の可能性。意図的な言及なら body_id_ignore に追加する）",
                line=lineno
            ))

    return findings

# ---------------------------------------------------------------------------
# ソースコード側の検査
# ---------------------------------------------------------------------------

def check_sources(
        paths: list[str],
        need_ids: Optional[set[str]],
) -> "tuple[list[Finding], set[str]]":
    """ソース群から @satisfies を抽出し、参照 ID を検査する。
    
    Args:
        paths: 走査対象ファイル一覧。
        need_ids: needs.json 由来の ID 集合（None なら実在検査をスキップ）。

    Returns:
        （検出結果一覧, ソース中で参照されていた ID の集合）のタプル。
    """
    findings: list[Finding] = []
    satisfied: set[str] = set()
    for path in paths:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for lineno, line in enumerate(f, start=1):
                for m in SATISFIES_RE.finditer(line):
                    ref: str = m.group(1)
                    satisfied.add(ref)
                    if need_ids is not None and ref not in need_ids:
                        findings.append(Finding(
                            "SRC01", SEVERITY_ERROR, path,
                            f"@satisfies {ref} が needs.json に存在しません",
                            line= lineno))
    return findings, satisfied

def check_unsatisfied_needs(
        need_ids:  Optional[set[str]],
        satisfied: set[str],
        enabled: bool,
) -> list[Finding]:
    """どのソースからも参照されていない要件を情報として報告する。

    設計フェーズでは未実装要件が多数あるのが正常なので、深刻度は info。
    実装フェーズの網羅確認（/find-coverage-gaps 相当の簡易版）として使う。

    Args:
        need_ids: needs.json 由来の ID 集合。
        satisfied: ソース中で @satisfies 参照されていた ID 集合。
        enabled: False なら何も報告しない。

    Returns:
        検出結果の一覧（深刻度 info）。
    """
    if not enabled or need_ids is None:
        return []
    findings: list[Finding] = []
    for need_id in sorted(need_ids - satisfied):
        findings.append(Finding(
            "XR01", SEVERITY_INFO, "(needs.json)",
            f"{need_id} を @satisfies するソースがまだありません"))
    return findings

# ---------------------------------------------------------------------------
# 出力と main
# ---------------------------------------------------------------------------

def render_text(findings: list[Finding]) -> str:
    """検出結果を人間向けテキストに整形する。

    Args:
        findings: 検出結果の一覧。

    Returns:
        整形済みの複数行文字列。
    """
    if not findings:
        return "OK: 検出なし"
    lines: list[str] = []
    order: dict[str, int] = {SEVERITY_ERROR: 0, SEVERITY_WARNING: 1, SEVERITY_INFO: 2}
    for f in sorted(findings, key=lambda x: (order[x.severity], x.path, x.rule)):
        loc: str = f"{f.path}:{f.line}" if f.line is not None else f.path
        lines.append(f"[{f.severity.upper():7s}] {f.rule} {loc}: {f.message}")
    n_err: int = sum(1 for f in findings if f.severity == SEVERITY_ERROR)
    n_warn: int = sum(1 for f in findings if f.severity == SEVERITY_WARNING)
    n_info: int = sum(1 for f in findings if f.severity == SEVERITY_INFO)
    lines.append(f"---- error: {n_err} / warning: {n_warn} / info: {n_info}")
    return "\n".join(lines)

def main() -> None:
    """引数を解釈して全検査を実行し、終了コードで結果を返す。
    
    Raises:
        SystemExit: 検査結果・入力不備に応じた終了コード（モジュール docstring の「終了コード」参照）。
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="frontmatter・@satisfies・ID 参照のメタデータ linter")
    parser.add_argument("--config", required=True, help="設定 YAML のパス")
    parser.add_argument("--format", choices=["text", "json"], default="text",help="出力形式（既定: text）")
    parser.add_argument("--strict", action="store_true", help="warning もエラー扱いにする")
    args: argparse.Namespace = parser.parse_args()

    cfg: Config = load_config(args.config)
    need_ids: Optional[set[str]] = load_needs_ids(cfg.needs_json)

    findings: list[Finding] = []

    md_files: list[str] = collect_files(cfg.docs_globs, cfg.docs_exclude)
    for path in md_files:
        findings.extend(check_markdown(path, cfg, need_ids))

    src_files: list[str] = collect_files(cfg.src_globs, [])
    src_findings: list[Finding]
    satisfied: set[str]
    src_findings, satisfied = check_sources(src_files, need_ids)
    findings.extend(src_findings)
    findings.extend(check_unsatisfied_needs(
        need_ids, satisfied, cfg.report_unsatisfied_needs))

    if args.format == "json":
        print(json.dumps(
            {"findings": [f.to_dict() for f in findings]},
            ensure_ascii=False, indent=2))
    else:
        print(render_text(findings))

    has_error: bool = any(f.severity == SEVERITY_ERROR for f in findings)
    has_warning: bool = any(f.severity == SEVERITY_WARNING for f in findings)
    if has_error or (args.strict and has_warning):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
