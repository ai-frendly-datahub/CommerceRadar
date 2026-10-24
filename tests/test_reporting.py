from datetime import date
from pathlib import Path

from flomers_kg.reporting import build_report_payload, write_report_artifacts


ROOT = Path(__file__).resolve().parents[1]


def test_build_report_payload_generates_dashboard_summary_fields():
    payload = build_report_payload(ROOT, report_date=date(2026, 4, 28))

    assert payload["category"] == "commerce"
    assert payload["date"] == "2026-04-28"
    assert payload["article_count"] == 0
    assert payload["match_candidate_count"] >= 1
    assert payload["matched_count"] <= payload["match_candidate_count"]
    assert payload["source_count"] == 4
    assert payload["collected_source_count"] == 0
    assert payload["supported_evidence_count"] == payload["match_candidate_count"]
    assert payload["pending_evidence_count"] == 0
    assert payload["sources"] == {}
    assert "sample_product_page" not in payload["sources"]
    assert payload["top_entities"]
    assert payload["warnings"] == []


def test_zero_public_collection_is_not_filled_with_sample_sources():
    payload = build_report_payload(
        ROOT,
        report_date=date(2026, 4, 28),
        collection={
            "article_count": 2,
            "source_count": 4,
            "collected_source_count": 3,
            "sources": {
                "sample_product_page": 2,
                "sample_distributor_page": 2,
                "sample_seller_channel": 2,
                "kosis": 0,
            },
            "results": [{"id": "sample_trend", "status": "ok", "count": 2}],
        },
    )

    assert payload["article_count"] == 0
    assert payload["collected_source_count"] == 0
    assert payload["sources"] == {"kosis": 0}
    assert "sample_product_page" not in payload["sources"]
    assert all(not str(row.get("id", "")).startswith("sample_") for row in payload["collection_results"])
    assert "공개 출처 수집 0건. 샘플 출처로 채우지 않음" in payload["warnings"]


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


def test_public_collection_does_not_promote_sample_matches_or_evidence():
    demo = build_report_payload(ROOT, report_date=date(2026, 10, 22))
    assert demo["data_scope"] == "sample_demo"
    assert demo["match_candidate_count"] == 2
    payload = build_report_payload(
        ROOT, report_date=date(2026, 10, 22),
        collection={"article_count": 35, "source_count": 4, "sources": {"kosis": 13}},
    )
    assert payload["data_scope"] == "public_collection"
    assert payload["matching_scope"] == "not_evaluated"
    assert payload["article_count"] == 35
    for key in ["match_candidate_count", "matched_count", "supported_evidence_count", "pending_evidence_count"]:
        assert payload[key] == 0
    assert payload["cards"] == []
    assert payload["top_entities"] == []
    assert payload["distributor_distribution"] == {}


def test_public_report_does_not_read_sample_seeds(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "sources.yaml").write_text("sources: []", encoding="utf-8")
    sample_dir = tmp_path / "data" / "samples"
    sample_dir.mkdir(parents=True)
    (sample_dir / "manufacturers.jsonl").write_text("not JSON", encoding="utf-8")
    payload = build_report_payload(tmp_path, collection={"article_count": 0})
    assert payload["cards"] == []
