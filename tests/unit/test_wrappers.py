from datetime import date
from pathlib import Path

import pytest

from commerceradar import analyzer
from commerceradar.reporter import _project_root as reporter_project_root
from commerceradar.reporter import generate_index_html, generate_report
from commerceradar.storage import RadarStorage
from flomers_kg.extraction_templates import (
    DISTRIBUTOR_PORTFOLIO_TEMPLATE,
    MANUFACTURER_PRODUCT_TEMPLATE,
    SELLER_PORTFOLIO_TREND_TEMPLATE,
)


SAMPLE_FILES = [
    "manufacturers.jsonl",
    "products.jsonl",
    "distributors.jsonl",
    "sellers.jsonl",
    "trends.jsonl",
    "evidence_records.jsonl",
    "transactions.jsonl",
]


def _report_root(tmp_path: Path) -> Path:
    sample_dir = tmp_path / "data" / "samples"
    sample_dir.mkdir(parents=True)
    for name in SAMPLE_FILES:
        (sample_dir / name).write_text("", encoding="utf-8")
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "sources.yaml").write_text("sources: []\n", encoding="utf-8")
    return tmp_path


@pytest.mark.unit
def test_analyzer_reexports_apply_entity_rules() -> None:
    assert analyzer.__all__ == ["apply_entity_rules"]
    assert callable(analyzer.apply_entity_rules)


@pytest.mark.unit
def test_reporter_project_root_points_to_repository() -> None:
    assert (reporter_project_root() / "pyproject.toml").is_file()


@pytest.mark.unit
def test_reporter_generates_report_and_index(tmp_path: Path) -> None:
    root = _report_root(tmp_path)

    paths = generate_report(project_root=root, report_date=date(2026, 5, 21))
    index_path = generate_index_html(project_root=root)

    assert paths["summary"].is_file()
    assert paths["report"].is_file()
    assert paths["index"].is_file()
    assert index_path == root / "reports" / "index.html"


@pytest.mark.unit
def test_storage_snapshot_methods_fail_closed(tmp_path: Path) -> None:
    storage = RadarStorage(tmp_path / "missing.duckdb")

    assert storage.create_daily_snapshot() is None
    assert storage.cleanup_old_snapshots() == 0


@pytest.mark.unit
def test_extraction_templates_include_expected_contract_fields() -> None:
    assert MANUFACTURER_PRODUCT_TEMPLATE["specs"]["package_type"] == ""
    assert "source_urls" in MANUFACTURER_PRODUCT_TEMPLATE
    assert DISTRIBUTOR_PORTFOLIO_TEMPLATE["trade_types"]["consignment"] is None
    assert "commerce_capability" in SELLER_PORTFOLIO_TREND_TEMPLATE
    assert SELLER_PORTFOLIO_TREND_TEMPLATE["social_metrics"]["followers"] is None
