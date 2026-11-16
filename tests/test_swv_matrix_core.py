"""swv_matrix_core のユニットテスト（#78）。"""
from __future__ import annotations

import copy
from typing import Any

import pytest
import yaml

from swv_matrix_core import Cell, MatrixSpecError, cell_id, enumerate_cells, parse_spec

# 2 行 × 2 列の最小構成（LCD Driver のマトリクスを縮めたもの）
BASE: dict[str, Any] = {
    "rows": {
        "label": "状態",
        "values": {"NORMAL": "正常", "ERROR": "エラー"},
    },
    "columns": {
        "label": "イベント",
        "values": {"REQOK": "表示要求（応答可）", "INTNG": "内部送信の失敗"},
    },
    "cells": {
        "NORMAL.INTNG": {"disposition": "not_applicable", "rationale": "内部送信はエラー状態に限られる"},
        "ERROR.REQOK": {"expected": "即座に失敗を返す", "tbd_items": "TBD-021"},
        "ERROR.INTNG": {"disposition": "undefined", "tbd_items": "TBD-020"},
    },
}

# cells を省略した本文。重複キー・真偽値キーの検査にも使う（辞書からは作れないため文字列で持つ）
AXES_ONLY: str = """\
rows:
  label: 状態
  values:
    NORMAL: 正常
columns:
  label: イベント
  values:
    REQOK: 表示要求（応答可）
"""

DELETE: object = object()


def to_text(spec: dict[str, Any]) -> str:
    """辞書を directive の本文（YAML）に変換する。"""
    return yaml.safe_dump(spec, allow_unicode=True, sort_keys=False)


def mutated(path: tuple[str, ...], value: Any) -> str:
    """BASE の path の位置を value に置き換えた本文を返す。value が DELETE なら削除する。"""
    spec: dict[str, Any] = copy.deepcopy(BASE)
    parent: dict[str, Any] = spec
    for key in path[:-1]:
        parent = parent[key]
    if value is DELETE:
        del parent[path[-1]]
    else:
        parent[path[-1]] = value
    return to_text(spec)


def cells_by_id(spec: dict[str, Any]) -> dict[str, Cell]:
    """仕様記述からセルを生成し、ID で引ける形にする。"""
    return {cell.id: cell for cell in enumerate_cells("SWVM_001", parse_spec(to_text(spec)))}


# ---------------------------------------------------------------------------
# セルの生成
# ---------------------------------------------------------------------------


def test_generates_all_combinations_in_row_major_order() -> None:
    """宣言の有無に関わらず、行数 × 列数 のセルを行優先で生成する。"""
    cells: list[Cell] = enumerate_cells("SWVM_001", parse_spec(to_text(BASE)))
    assert [cell.id for cell in cells] == [
        "SWVC_001_NORMAL_REQOK",
        "SWVC_001_NORMAL_INTNG",
        "SWVC_001_ERROR_REQOK",
        "SWVC_001_ERROR_INTNG",
    ]


def test_undeclared_cell_is_verified() -> None:
    """cells に書かないセルは verified（検証ケースが必要）になる。"""
    assert cells_by_id(BASE)["SWVC_001_NORMAL_REQOK"] == Cell(
        id="SWVC_001_NORMAL_REQOK", row_key="NORMAL", col_key="REQOK",
        row="正常", column="表示要求（応答可）", disposition="verified",
    )


def test_cells_can_be_omitted() -> None:
    """cells を省略したマトリクスは、全てのセルが verified になる。"""
    cells: list[Cell] = enumerate_cells("SWVM_001", parse_spec(AXES_ONLY))
    assert [(cell.id, cell.disposition) for cell in cells] == [("SWVC_001_NORMAL_REQOK", "verified")]


def test_declared_attributes_are_carried_to_cells() -> None:
    """cells に書いた属性がセルに引き継がれる。disposition を省略すれば verified。"""
    cells: dict[str, Cell] = cells_by_id(BASE)
    na: Cell = cells["SWVC_001_NORMAL_INTNG"]
    assert (na.disposition, na.rationale) == ("not_applicable", "内部送信はエラー状態に限られる")
    partial: Cell = cells["SWVC_001_ERROR_REQOK"]
    assert (partial.disposition, partial.expected, partial.tbd_items) == (
        "verified", "即座に失敗を返す", "TBD-021")
    undefined: Cell = cells["SWVC_001_ERROR_INTNG"]
    assert (undefined.disposition, undefined.tbd_items) == ("undefined", "TBD-020")


def test_title_is_row_label_times_column_label() -> None:
    """タイトルは「行ラベル × 列ラベル」。"""
    assert cells_by_id(BASE)["SWVC_001_ERROR_INTNG"].title == "エラー × 内部送信の失敗"


def test_cell_ids_do_not_depend_on_axis_order() -> None:
    """軸の値の並び順を変えても、各 ID が指すセルは変わらない（連番にしない理由）。"""
    reordered: dict[str, Any] = copy.deepcopy(BASE)
    for axis in ("rows", "columns"):
        reordered[axis]["values"] = dict(reversed(BASE[axis]["values"].items()))
    before: dict[str, Cell] = cells_by_id(BASE)
    after: dict[str, Cell] = cells_by_id(reordered)
    assert list(before) != list(after)
    assert before == after


def test_cell_id_is_built_from_matrix_number_and_keys() -> None:
    """セルの ID はマトリクスの番号と行・列のキーから作る。"""
    assert cell_id("SWVM_001", "ERROR", "REQOK") == "SWVC_001_ERROR_REQOK"


@pytest.mark.parametrize("matrix_id", ["SWVM001", "SWVM_1", "SWV_001", "SWVM_001_A"])
def test_cell_id_rejects_malformed_matrix_id(matrix_id: str) -> None:
    """マトリクスの ID が SWVM_NNN の形でなければ拒否する。"""
    with pytest.raises(MatrixSpecError, match="SWVM_NNN"):
        cell_id(matrix_id, "ERROR", "REQOK")


# ---------------------------------------------------------------------------
# 仕様記述の検証
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("path", "value", "message"),
    [
        pytest.param(("cell",), {}, "位置：本文", id="top-level-typo"),
        pytest.param(("rows",), DELETE, "rows がない", id="rows-missing"),
        pytest.param(("rows", "lable"), "状態", "'lable'", id="axis-key-typo"),
        pytest.param(("columns", "label"), DELETE, "columns.label がない", id="label-missing"),
        pytest.param(("rows", "values"), {}, "rows.values がない", id="values-empty"),
        pytest.param(("rows", "values", "normal"), "x", "キー 'normal' が不正", id="key-lowercase"),
        pytest.param(("rows", "values", "NORMAL_4"), "x", "キー 'NORMAL_4' が不正", id="key-underscore"),
        pytest.param(("rows", "values", "4NORMAL"), "x", "キー '4NORMAL' が不正", id="key-digit-first"),
        pytest.param(("rows", "values", "ERROR"), None, "ERROR の表示ラベルがない", id="value-label-missing"),
        pytest.param(("rows", "values", "ERROR"), "正常", "'正常' が重複", id="value-label-duplicate"),
        pytest.param(("cells",), ["NORMAL.REQOK"], "cells は", id="cells-not-mapping"),
        pytest.param(("cells", "NORMALREQOK"), {"expected": "x"}, "の形でない", id="cell-key-no-dot"),
        pytest.param(("cells", "BUSY.REQOK"), {"expected": "x"}, "行キー 'BUSY'", id="cell-unknown-row"),
        pytest.param(("cells", "NORMAL.REQNG"), {"expected": "x"}, "列キー 'REQNG'", id="cell-unknown-column"),
        pytest.param(("cells", "NORMAL.REQOK"), None, "属性がない", id="cell-without-attrs"),
        pytest.param(("cells", "NORMAL.INTNG", "rational"), "x", "'rational'", id="cell-attr-typo"),
        pytest.param(("cells", "ERROR.REQOK", "expected"), 1, "空でない文字列", id="cell-attr-not-string"),
        pytest.param(("cells", "NORMAL.INTNG", "disposition"), "n/a", "'n/a' が不正", id="cell-bad-disposition"),
    ],
)
def test_parse_spec_rejects_invalid_spec(path: tuple[str, ...], value: Any, message: str) -> None:
    """規則に反する記述を、原因が分かるメッセージとともに拒否する。"""
    with pytest.raises(MatrixSpecError, match=message):
        parse_spec(mutated(path, value))


@pytest.mark.parametrize(
    ("text", "message"),
    [
        pytest.param("", "マッピングで書く", id="empty"),
        pytest.param("rows: [\n", "YAML として解釈できない", id="yaml-syntax-error"),
        pytest.param(AXES_ONLY.replace("REQOK:", "ON:"), "引用符で囲む", id="yaml-boolean-key"),
        pytest.param(AXES_ONLY.replace("NORMAL: 正常", "NORMAL: 正常\n    NORMAL: エラー"),
                     "'NORMAL' が重複", id="duplicate-axis-key"),
        pytest.param(AXES_ONLY + "cells:\n  NORMAL.REQOK: {expected: a}\n  NORMAL.REQOK: {expected: b}\n",
                     "'NORMAL.REQOK' が重複", id="duplicate-cell"),
    ],
)
def test_parse_spec_rejects_invalid_text(text: str, message: str) -> None:
    """辞書では表せない誤り（YAML の構文、真偽値への変換、キーの重複）を拒否する。"""
    with pytest.raises(MatrixSpecError, match=message):
        parse_spec(text)
