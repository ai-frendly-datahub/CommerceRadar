from datetime import date
from pathlib import Path

from flomers_kg.reporting import build_report_payload, write_report_artifacts


ROOT = Path(__file__).resolve().parents[1]


def test_build_report_payload_generates_dashboard_summary_fields():
    payload = build_report_payload(ROOT, report_date=date(2026, 4, 28))

    assert payload["category"] == "commerce"
    assert payload["date"] == "2026-04-28"
    assert payload["article_count"] >= 1
    assert payload["matched_count"] <= payload["article_count"]
    assert payload["source_count"] == 8
    assert payload["collected_source_count"] >= 1
    assert payload["supported_evidence_count"] == payload["article_count"]
    assert payload["pending_evidence_count"] == 0
    assert "sample_product_page" in payload["sources"]
    assert payload["top_entities"]
    assert payload["warnings"] == []


def test_report_payload_has_no_pending_evidence_for_repository_samples():
    payload = build_report_payload(ROOT, report_date=date(2026, 4, 28))
    pending_cards = [
        card
        for card in payload["cards"]
        if any(str(evidence_id).startswith("evidence_pending::") for evidence_id in card["evidence_ids"])
    ]

    assert pending_cards == []
    assert all(card["evidence_status"] == "supported" for card in payload["cards"])
    assert all(card["breakdown"]["evidence_confidence"] > 0.0 for card in payload["cards"])


def test_write_report_artifacts_outputs_summary_report_and_index(tmp_path):
    paths = write_report_artifacts(ROOT, output_dir=tmp_path, report_date=date(2026, 4, 28))

    assert paths["summary"].name == "commerce_20260428_summary.json"
    assert paths["report"].name == "commerce_20260428.html"
    assert paths["index"].name == "index.html"
    assert paths["summary"].is_file()
    assert paths["report"].read_text(encoding="utf-8").startswith("<!doctype html>")
    assert "commerce_20260428.html" in paths["index"].read_text(encoding="utf-8")
