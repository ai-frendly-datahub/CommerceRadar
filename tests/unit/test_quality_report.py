import json
from datetime import date
from pathlib import Path

import pytest

from commerceradar.quality_report import (
    _evidence_validity_checks,
    build_quality_report,
    write_quality_report,
)


@pytest.mark.unit
def test_build_quality_report_handles_missing_summary(tmp_path: Path) -> None:
    payload = build_quality_report(tmp_path)

    assert payload["sources_enabled"] == 0
    assert payload["sources_fresh"] == 0
    assert payload["warnings"] == ["no commerce summary available"]
    assert payload["data_quality_checks"]["schema_error_count"] == 0


@pytest.mark.unit
def test_build_quality_report_uses_collected_source_count(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    summary = {
        "source_count": 8,
        "collected_source_count": 3,
        "sources": {"sample_product_page": 1},
        "article_count": 4,
        "matched_count": 2,
        "warnings": ["review pending"],
    }
    (reports_dir / "commerce_20260521_summary.json").write_text(
        json.dumps(summary), encoding="utf-8"
    )

    payload = build_quality_report(tmp_path)

    assert payload["sources_enabled"] == 8
    assert payload["sources_fresh"] == 3
    assert payload["daily_review_items"] == 2
    assert payload["pending_evidence_items"] == 0
    assert payload["warnings"] == ["review pending"]
    assert payload["summary_file"] == "commerce_20260521_summary.json"
    assert payload["data_quality_checks"]["reference_error_count"] == 0
    assert payload["data_quality_checks"]["low_quality_group_count"] == 0


@pytest.mark.unit
def test_write_quality_report_writes_json_payload(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "commerce_20260521_summary.json").write_text(
        json.dumps({"source_count": 1, "article_count": 1, "matched_count": 1}),
        encoding="utf-8",
    )

    out_path = write_quality_report(tmp_path)
    payload = json.loads(out_path.read_text(encoding="utf-8"))

    assert out_path == reports_dir / "commerce_quality.json"
    assert payload["category"] == "commerce"
    assert payload["summary_file"] == "commerce_20260521_summary.json"
    assert "data_quality_checks" in payload


@pytest.mark.unit
def test_build_quality_report_warns_on_reference_and_raw_duplicates(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "commerce_20260521_summary.json").write_text(
        json.dumps({"source_count": 1, "article_count": 1, "matched_count": 0}),
        encoding="utf-8",
    )
    sample_dir = tmp_path / "data" / "samples"
    sample_dir.mkdir(parents=True)
    (sample_dir / "manufacturers.jsonl").write_text("", encoding="utf-8")
    (sample_dir / "products.jsonl").write_text(
        '{"id":"p1","manufacturer_id":"missing","name":"P","category":"haircare"}\n',
        encoding="utf-8",
    )
    (sample_dir / "distributors.jsonl").write_text("", encoding="utf-8")
    (sample_dir / "sellers.jsonl").write_text("", encoding="utf-8")
    (sample_dir / "trends.jsonl").write_text("", encoding="utf-8")
    (sample_dir / "evidence_records.jsonl").write_text(
        '{"id":"ev1","source_type":"sample","confidence":0.5,"observed_at":"2026-05-21",'
        '"related_entities":["missing_entity"]}\n',
        encoding="utf-8",
    )
    (sample_dir / "transactions.jsonl").write_text(
        '{"id":"tx1","match_id":"match::m::p::d::s","status":"planned","started_at":"2026-05-21"}\n',
        encoding="utf-8",
    )
    raw_dir = tmp_path / "data" / "raw" / "2026-05-21"
    raw_dir.mkdir(parents=True)
    (raw_dir / "commerce_kg_trends.jsonl").write_text(
        '{"link":"https://example.com/a"}\n{"link":"https://example.com/a"}\n',
        encoding="utf-8",
    )

    payload = build_quality_report(tmp_path)

    checks = payload["data_quality_checks"]
    assert checks["reference_error_count"] >= 1
    assert checks["raw_trend_duplicate_link_count"] == 1
    assert "sample reference integrity errors exist" in payload["warnings"]
    assert "raw trend log contains duplicate links" in payload["warnings"]
    assert "sample quality score below threshold" in payload["warnings"]
    assert "raw trend log is missing KG trend ids" in payload["warnings"]
    assert "raw trend log is missing source observed dates" in payload["warnings"]
    assert "raw trend extraction quality below threshold" in payload["warnings"]


@pytest.mark.unit
def test_build_quality_report_accepts_enriched_raw_trends(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "commerce_20260521_summary.json").write_text(
        json.dumps({"source_count": 1, "article_count": 1, "matched_count": 1}),
        encoding="utf-8",
    )
    raw_dir = tmp_path / "data" / "raw" / "2026-05-21"
    raw_dir.mkdir(parents=True)
    (raw_dir / "commerce_kg_trends.jsonl").write_text(
        json.dumps(
            {
                "title": "Trend",
                "link": "https://example.com/trend",
                "summary": "hair oil",
                "published": "2026-05-21T00:00:00+00:00",
                "source": "sample_trend",
                "category": "commerce",
                "matched_entities": {
                    "Country": ["JP"],
                    "Channel": ["BASE"],
                    "Category": ["haircare"],
                },
                "ontology": {
                    "kg_entity": {"type": "Trend", "id": "t1"},
                    "source_meta": {"verified_at": "2026-05-21"},
                    "extraction": {"quality_score": 100.0, "observed_at": "2026-05-21"},
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = build_quality_report(tmp_path)
    checks = payload["data_quality_checks"]

    assert checks["raw_trend_missing_kg_id_count"] == 0
    assert checks["raw_trend_missing_entity_count"] == 0
    assert checks["raw_trend_missing_source_observed_at_count"] == 0
    assert checks["raw_trend_average_extraction_quality"] == 100.0
    assert "raw trend log is missing KG trend ids" not in payload["warnings"]
    assert "raw trend log is missing source observed dates" not in payload["warnings"]
    assert "raw trend extraction quality below threshold" not in payload["warnings"]


@pytest.mark.unit
def test_build_quality_report_warns_on_pending_evidence_count(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "commerce_20260521_summary.json").write_text(
        json.dumps(
            {
                "source_count": 1,
                "article_count": 2,
                "matched_count": 1,
                "pending_evidence_count": 1,
            }
        ),
        encoding="utf-8",
    )

    payload = build_quality_report(tmp_path)

    assert payload["pending_evidence_items"] == 1
    assert "match candidates have pending evidence" in payload["warnings"]


@pytest.mark.unit
def test_build_quality_report_includes_sample_quality_scores(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "commerce_20260521_summary.json").write_text(
        json.dumps({"source_count": 1, "article_count": 1, "matched_count": 1}),
        encoding="utf-8",
    )
    sample_dir = tmp_path / "data" / "samples"
    sample_dir.mkdir(parents=True)
    (sample_dir / "manufacturers.jsonl").write_text(
        (
            '{"id":"m1","name":"M","country":"KR","categories":["haircare"],'
            '"source":{"source_type":"sample","source_urls":["https://example.com"],'
            '"confidence_level":5,"verified_at":"2026-05-21"}}\n'
        ),
        encoding="utf-8",
    )

    payload = build_quality_report(tmp_path)
    checks = payload["data_quality_checks"]

    assert checks["average_quality_by_kind"]["manufacturers"] >= 70
    assert checks["minimum_quality_by_kind"]["manufacturers"] >= 70


@pytest.mark.unit
def test_repository_sample_quality_report_has_no_quality_warnings() -> None:
    root = Path(__file__).resolve().parents[2]

    payload = build_quality_report(root)

    checks = payload["data_quality_checks"]
    assert checks["low_quality_group_count"] == 0
    assert checks["evidence_expiring_soon_count"] == 0
    assert checks["evidence_expired_count"] == 0
    assert payload["pending_evidence_items"] == 0
    assert "sample quality score below threshold" not in payload["warnings"]
    assert "evidence records are expired or expiring soon" not in payload["warnings"]
    assert "match candidates have pending evidence" not in payload["warnings"]


@pytest.mark.unit
def test_evidence_validity_checks_find_expiring_and_expired_records(tmp_path: Path) -> None:
    sample_dir = tmp_path / "data" / "samples"
    sample_dir.mkdir(parents=True)
    (sample_dir / "evidence_records.jsonl").write_text(
        (
            '{"id":"ev_expiring","valid_until":"2026-05-28"}\n'
            '{"id":"ev_expired","valid_until":"2026-05-01"}\n'
            '{"id":"ev_ok","valid_until":"2026-07-01"}\n'
        ),
        encoding="utf-8",
    )

    checks = _evidence_validity_checks(tmp_path, today=date(2026, 5, 21))

    assert checks["evidence_expiring_soon_ids"] == ["ev_expiring"]
    assert checks["evidence_expired_ids"] == ["ev_expired"]
