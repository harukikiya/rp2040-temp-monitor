"""swvmatrix の仕様記述を解釈し、検証条件（swvcond）のセルを列挙する。

Sphinx に依存しない部分を集めたモジュール。directive と表の描画は
swv_matrix.py が担い、本モジュールは pytest でユニットテストを行う（#78）。

仕様記述（swvmatrix directive の本文）の形式：

    rows:
      label: 状態
      values:
        NORMAL: 正常
        ERROR: エラー
    columns:
      label: イベント
      values:
        REQOK: 表示要求（応答可）
    cells:
      ERROR.REQOK:
        expected: 即座に失敗を返す

cells に宣言しないセルは disposition: verified（検証ケースが必要）とする。
"""
from __future__ import annotations

import dataclasses
import re
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

# 軸の値のキー。"_" と "." を禁じることで、セル ID とセル指定を一意に分解できる
KEY_RE: re.Pattern[str] = re.compile(r"[A-Z][A-Z0-9]*")

# マトリクスの ID。番号部分をセルの ID に引き継ぐ
MATRIX_ID_RE: re.Pattern[str] = re.compile(r"SWVM_([0-9]{3})")

DISPOSITIONS: frozenset[str] = frozenset({"verified", "not_applicable", "undefined"})
DEFAULT_DISPOSITION: str = "verified"

TOP_KEYS: frozenset[str] = frozenset({"rows", "columns", "cells"})
AXIS_KEYS: frozenset[str] = frozenset({"label", "values"})
CELL_KEYS: frozenset[str] = frozenset({"disposition", "expected", "rationale", "tbd_items"})

# ---------------------------------------------------------------------------
# データ型
# ---------------------------------------------------------------------------


class MatrixSpecError(ValueError):
    """仕様記述の誤り。directive がビルドエラーとして報告する。"""


@dataclasses.dataclass(frozen=True)
class Axis:
    """マトリクスの軸（行または列）。

    Attributes:
        label: 軸の見出し（例：状態）。
        values: キーから表示ラベルへの対応。記述した順序を保つ。
    """

    label: str
    values: dict[str, str]


@dataclasses.dataclass(frozen=True)
class MatrixSpec:
    """検証済みの仕様記述。

    Attributes:
        rows: 行の軸。
        columns: 列の軸。
        cells: (行キー, 列キー) からセルの属性への対応。宣言したセルのみを持つ。
    """

    rows: Axis
    columns: Axis
    cells: dict[tuple[str, str], dict[str, str]]


@dataclasses.dataclass(frozen=True)
class Cell:
    """生成する検証条件（swvcond）1件分。

    Attributes:
        id: need の ID（例：SWVC_001_ERROR_REQOK）。
        row_key: 行のキー。
        col_key: 列のキー。
        row: 行の表示ラベル。
        column: 列の表示ラベル。
        disposition: verified / not_applicable / undefined のいずれか。
        expected: 期待結果。need の本文になる。未記載なら空文字列。
        rationale: 根拠。未記載なら None。
        tbd_items: 未確定項目。未記載なら None。
    """

    id: str
    row_key: str
    col_key: str
    row: str
    column: str
    disposition: str
    expected: str = ""
    rationale: str | None = None
    tbd_items: str | None = None

    @property
    def title(self) -> str:
        """need のタイトル（「行ラベル × 列ラベル」）。"""
        return f"{self.row} × {self.column}"


class _UniqueKeyLoader(yaml.SafeLoader):
    """同じマッピング内のキーの重複を誤りとして扱う SafeLoader。

    PyYAML は重複したキーを後勝ちで黙って上書きする。軸の値のキーが重複すると
    行や列が1つ消え、消えたセルはどの needs_warnings にも掛からないため拒否する。
    マージキー（<<）で取り込んだキーの上書きも、同じ理由で重複として扱う。
    """

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        """マッピングを構築し、キーの重複があれば例外を送出する。

        Args:
            node: YAML のマッピングノード。
            deep: 入れ子のオブジェクトを即座に構築するか。

        Returns:
            構築した辞書。

        Raises:
            MatrixSpecError: キーが重複している場合。
        """
        mapping: dict[Any, Any] = super().construct_mapping(node, deep=deep)
        if len(mapping) < len(node.value):
            seen: set[Any] = set()
            for key_node, _ in node.value:
                key: Any = self.construct_object(key_node, deep=deep)
                if key in seen:
                    raise MatrixSpecError(
                        f"キー {key!r} が重複している（本文の {key_node.start_mark.line + 1} 行目）")
                seen.add(key)
        return mapping


# ---------------------------------------------------------------------------
# 仕様記述の解釈
# ---------------------------------------------------------------------------


def parse_spec(text: str) -> MatrixSpec:
    """swvmatrix directive の本文を解釈し、規則に照らして検証する。

    Args:
        text: directive の本文（YAML）。

    Returns:
        検証済みの仕様記述。

    Raises:
        MatrixSpecError: YAML として解釈できない場合、または規則に反する場合。
    """
    try:
        data: Any = yaml.load(text, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as e:
        raise MatrixSpecError(f"YAML として解釈できない：{e}") from e
    if not isinstance(data, dict):
        raise MatrixSpecError("本文は rows / columns / cells を持つマッピングで書く")
    _reject_unknown_keys(data, TOP_KEYS, "本文")
    rows: Axis = _parse_axis(data, "rows")
    columns: Axis = _parse_axis(data, "columns")
    cells: dict[tuple[str, str], dict[str, str]] = _parse_cells(data.get("cells"), rows, columns)
    return MatrixSpec(rows=rows, columns=columns, cells=cells)


def _reject_unknown_keys(mapping: dict[Any, Any], allowed: frozenset[str], where: str) -> None:
    """許可されていないキーがあれば例外を送出する（誤記の検出）。

    Args:
        mapping: 検査するマッピング。
        allowed: 許可するキーの集合。
        where: エラーメッセージに使う位置の名前。

    Raises:
        MatrixSpecError: 許可されていないキーがある場合。
    """
    unknown: list[Any] = [key for key in mapping if key not in allowed]
    if unknown:
        raise MatrixSpecError(
            f"未知のキー {unknown!r} がある（位置：{where}、使えるキー：{', '.join(sorted(allowed))}）")


def _parse_axis(data: dict[Any, Any], name: str) -> Axis:
    """軸（rows または columns）を解釈する。

    Args:
        data: 本文全体のマッピング。
        name: 軸の名前（rows / columns）。

    Returns:
        検証済みの軸。

    Raises:
        MatrixSpecError: 軸の記述が規則に反する場合。
    """
    axis: Any = data.get(name)
    if not isinstance(axis, dict):
        raise MatrixSpecError(f"{name} がない（label と values を持つマッピングで書く）")
    _reject_unknown_keys(axis, AXIS_KEYS, name)
    label: Any = axis.get("label")
    if not isinstance(label, str) or not label:
        raise MatrixSpecError(f"{name}.label がない")
    raw: Any = axis.get("values")
    if not isinstance(raw, dict) or not raw:
        raise MatrixSpecError(f"{name}.values がない（キーと表示ラベルの組を1つ以上書く）")
    values: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            raise MatrixSpecError(
                f"{name}.values のキー {key!r} が文字列でない"
                "（YAML は ON / OFF / YES / NO などを真偽値に変換する。引用符で囲む）")
        if not KEY_RE.fullmatch(key):
            raise MatrixSpecError(
                f"{name}.values のキー {key!r} が不正"
                "（英大文字で始め、英大文字と数字のみで書く。_ と . は使えない）")
        if not isinstance(value, str) or not value:
            raise MatrixSpecError(f"{name}.values.{key} の表示ラベルがない")
        if value in values.values():
            raise MatrixSpecError(f"{name}.values の表示ラベル {value!r} が重複している")
        values[key] = value
    return Axis(label=label, values=values)


def _parse_cells(raw: Any, rows: Axis, columns: Axis) -> dict[tuple[str, str], dict[str, str]]:
    """cells（セルごとの例外指定）を解釈する。

    Args:
        raw: cells の値。記述がなければ None。
        rows: 検証済みの行の軸。
        columns: 検証済みの列の軸。

    Returns:
        (行キー, 列キー) から属性への対応。

    Raises:
        MatrixSpecError: セルの記述が規則に反する場合。
    """
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise MatrixSpecError("cells は「行キー.列キー」をキーとするマッピングで書く")
    cells: dict[tuple[str, str], dict[str, str]] = {}
    for spec_key, attrs in raw.items():
        if not isinstance(spec_key, str) or spec_key.count(".") != 1:
            raise MatrixSpecError(f"セル指定 {spec_key!r} が「行キー.列キー」の形でない")
        row_key, col_key = spec_key.split(".")
        if row_key not in rows.values:
            raise MatrixSpecError(f"セル指定 {spec_key!r} の行キー {row_key!r} が rows に宣言されていない")
        if col_key not in columns.values:
            raise MatrixSpecError(f"セル指定 {spec_key!r} の列キー {col_key!r} が columns に宣言されていない")
        where: str = f"cells.{spec_key}"
        if not isinstance(attrs, dict) or not attrs:
            raise MatrixSpecError(f"{where} に属性がない")
        _reject_unknown_keys(attrs, CELL_KEYS, where)
        for attr, value in attrs.items():
            if not isinstance(value, str) or not value:
                raise MatrixSpecError(f"{where}.{attr} は空でない文字列で書く")
        disposition: str = attrs.get("disposition", DEFAULT_DISPOSITION)
        if disposition not in DISPOSITIONS:
            raise MatrixSpecError(
                f"{where}.disposition {disposition!r} が不正（{', '.join(sorted(DISPOSITIONS))} のいずれか）")
        cells[(row_key, col_key)] = dict(attrs)
    return cells


# ---------------------------------------------------------------------------
# セルの生成
# ---------------------------------------------------------------------------


def cell_id(matrix_id: str, row_key: str, col_key: str) -> str:
    """セルの need ID を作る。

    ID は軸の値のキーから作り、連番にしない。軸の値の並び順を変えても ID は変わらない。

    Args:
        matrix_id: マトリクスの ID（例：SWVM_001）。
        row_key: 行のキー。
        col_key: 列のキー。

    Returns:
        セルの ID（例：SWVC_001_ERROR_REQOK）。

    Raises:
        MatrixSpecError: matrix_id が SWVM_NNN の形でない場合。
    """
    match: re.Match[str] | None = MATRIX_ID_RE.fullmatch(matrix_id)
    if match is None:
        raise MatrixSpecError(f"マトリクスの ID {matrix_id!r} が SWVM_NNN の形でない")
    return f"SWVC_{match.group(1)}_{row_key}_{col_key}"


def enumerate_cells(matrix_id: str, spec: MatrixSpec) -> list[Cell]:
    """行と列の全ての組み合わせについてセルを作る。

    並びは行優先で、仕様記述に書いた順序に従う。cells に宣言していないセルは
    disposition: verified とする。

    Args:
        matrix_id: マトリクスの ID（例：SWVM_001）。
        spec: parse_spec が返した仕様記述。

    Returns:
        行数 × 列数 件のセル。

    Raises:
        MatrixSpecError: matrix_id が SWVM_NNN の形でない場合。
    """
    cells: list[Cell] = []
    for row_key, row in spec.rows.values.items():
        for col_key, column in spec.columns.values.items():
            attrs: dict[str, str] = spec.cells.get((row_key, col_key), {})
            cells.append(Cell(
                id=cell_id(matrix_id, row_key, col_key),
                row_key=row_key,
                col_key=col_key,
                row=row,
                column=column,
                disposition=attrs.get("disposition", DEFAULT_DISPOSITION),
                expected=attrs.get("expected", ""),
                rationale=attrs.get("rationale"),
                tbd_items=attrs.get("tbd_items"),
            ))
    return cells
