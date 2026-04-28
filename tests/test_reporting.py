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
    assert payload["top_entities"]
    assert payload["warnings"] == []


def test_write_report_artifacts_outputs_summary_report_and_index(tmp_path):
    paths = write_report_artifacts(ROOT, output_dir=tmp_path, report_date=date(2026, 4, 28))

    assert paths["summary"].name == "commerce_20260428_summary.json"
    assert paths["report"].name == "commerce_20260428.html"
    assert paths["index"].name == "index.html"
    assert paths["summary"].is_file()
    assert paths["report"].read_text(encoding="utf-8").startswith("<!doctype html>")
    assert "commerce_20260428.html" in paths["index"].read_text(encoding="utf-8")
