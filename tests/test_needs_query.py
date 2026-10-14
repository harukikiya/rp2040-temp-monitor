"""needs_query.py のテスト - 小さな fixture で取得・検索・トレース・集計を確かめる。"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
import needs_query as nq

FIXTURE: Path = Path(__file__).parent / "fixtures" / "needs_mini.json"

@pytest.fixture
def store() -> nq.NeedsStore:
    """fixture の needs.json（8 件）を読み込んだストア。"""
    return nq.load_needs(FIXTURE)

def test_load_pick_current_version(store: nq.NeedsStore) -> None:
    assert len(store.needs) == 8
    assert store.built_at == "2026-09-28T10:00:00"

def test_missing_file_tells_how_to_fix(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="make rebuild"):
        nq.load_needs(tmp_path / "needs.json")

def test_get_need_drops_internal_fields(store: nq.NeedsStore) -> None:
    detail = nq.get_need(store, "SWR_001")
    assert detail["title"] == "ADCで温度センサを読む"
    assert "avatar" not in detail
    assert "jinja_content" not in detail
    assert detail["upstream"] == {"refines": ["SYS_001"]}
    assert detail["downstream"] == {"verifies_back": ["SWV_001", "SWV_002"]}
    assert detail["source"] == "docs/common/20_software_requirements.md:12"

def test_get_need_accepts_lowercase(store: nq.NeedsStore) -> None:
    assert nq.get_need(store, " swr_001 ")["id"] == "SWR_001"

def test_unknown_id_suggests_close_ids(store: nq.NeedsStore) -> None:
    with pytest.raises(nq.NeedNotFoundError, match="近い ID: SWR_00"):
        nq.get_need(store, "SWR_004")

def test_search_filters_combine(store: nq.NeedsStore) -> None:
    result = nq.search_needs(store, need_type="swreq", status="draft")
    assert [n["id"] for n in result["needs"]] == ["SWR_002"]

def test_search_text_is_case_insensitive(store: nq.NeedsStore) -> None:
    result = nq.search_needs(store, text="adc")
    assert [n["id"] for n in result["needs"]] == ["SWR_001", "SWV_001"]

def test_search_truncates_at_limit(store: nq.NeedsStore) -> None:
    result = nq.search_needs(store, limit=3)
    assert result["count"] == 8
    assert len(result["needs"]) == 3
    assert result["truncated"] is True

def test_trace_down_follows_refines_and_verifines(store: nq.NeedsStore) -> None:
    result = nq.trace(store, "SYS_001", direction="down")
    depth_of = {n["id"]: n["depth"] for n in result["downstream"]}
    assert depth_of == {
        "ARC_001": 1, "SWR_001": 1, "SWR_002": 1,"SWR_003": 1,
        "ARC_002": 2, "SWV_001": 2, "SWV_002": 2,
    }
    assert "upstream" not in result

def test_trace_up_from_a_verification_case(store: nq.NeedsStore) -> None:
    result = nq.trace(store, "SWV_001", direction="up")
    assert [(n["id"], n["via"], n["depth"]) for n in result["upstream"]] == [
        ("SWR_001", "verifies", 1),
        ("SYS_001", "refines", 2),
    ]

def test_trace_respects_max_depth(store: nq.NeedsStore) -> None:
    result = nq.trace(store, "SYS_001", direction="down", max_depth=1)
    assert {n["depth"] for n in result["downstream"]} == {1}

def test_status_report(store: nq.NeedsStore) -> None:
    report = nq.status_report(store)
    assert report["counts"]["swreq"] == {"approved": 1, "draft": 1, "obsolete": 1}
    #obsolete の SWR_003 は検証不要なので数えない
    assert report["swreq_without_verification"] == ["SWR_002"]
    assert list(report["tbd_items"]) == ["SWR_002"]
    assert report["open_params"] == ["SWR_001"]
    assert report["swverif_by_environment"] == {"target": 1, "host": 1}

def test_newer_source_is_reported_as_stale(tmp_path: Path) -> None:
    needs_json = tmp_path / "needs.json"
    needs_json.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    source = docs / "20_software_requirements.md"
    source.write_text("# SWR\n", encoding="utf-8")
    built = needs_json.stat().st_mtime

    os.utime(source, (built + 60, built + 60))  # 原稿の方が 60 秒新しい
    assert nq.load_needs(needs_json, docs).stale_sources == ("20_software_requirements.md",)

    os.utime(source, (built - 60, built - 60))  # 原稿の方が古い = 最新
    assert nq.load_needs(needs_json, docs).stale_sources == ()
