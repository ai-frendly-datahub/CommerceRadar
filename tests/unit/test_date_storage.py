from datetime import date
from pathlib import Path

import pytest

from commerceradar.date_storage import (
    apply_date_storage_policy,
    cleanup_dated_files,
    materialize_kg_raw_snapshot,
)


@pytest.mark.unit
def test_cleanup_dated_files_removes_old_date_named_files(tmp_path: Path) -> None:
    old_file = tmp_path / "commerce_20260101_summary.json"
    fresh_file = tmp_path / "commerce_20260520_summary.json"
    undated_file = tmp_path / "index.html"
    old_file.write_text("old", encoding="utf-8")
    fresh_file.write_text("fresh", encoding="utf-8")
    undated_file.write_text("index", encoding="utf-8")

    removed = cleanup_dated_files(tmp_path, keep_days=30, today=date(2026, 5, 21))

    assert removed == 1
    assert not old_file.exists()
    assert fresh_file.exists()
    assert undated_file.exists()


@pytest.mark.unit
def test_cleanup_dated_files_handles_iso_date_names(tmp_path: Path) -> None:
    old_file = tmp_path / "2026-01-01-radar.duckdb"
    fresh_file = tmp_path / "2026-05-20-radar.duckdb"
    old_file.write_text("old", encoding="utf-8")
    fresh_file.write_text("fresh", encoding="utf-8")

    removed = cleanup_dated_files(tmp_path, keep_days=30, today=date(2026, 5, 21))

    assert removed == 1
    assert not old_file.exists()
    assert fresh_file.exists()


@pytest.mark.unit
def test_cleanup_dated_files_ignores_negative_retention(tmp_path: Path) -> None:
    old_file = tmp_path / "commerce_20260101_summary.json"
    old_file.write_text("old", encoding="utf-8")

    removed = cleanup_dated_files(tmp_path, keep_days=-1, today=date(2026, 5, 21))

    assert removed == 0
    assert old_file.exists()


@pytest.mark.unit
def test_materialize_kg_raw_snapshot_copies_sample_jsonl(tmp_path: Path) -> None:
    sample_dir = tmp_path / "data" / "samples"
    sample_dir.mkdir(parents=True)
    (sample_dir / "trends.jsonl").write_text('{"id":"t1"}\n', encoding="utf-8")
    (sample_dir / "notes.txt").write_text("ignored", encoding="utf-8")

    raw_dir = materialize_kg_raw_snapshot(tmp_path, snapshot_date=date(2026, 5, 21))

    assert raw_dir == tmp_path / "data" / "raw" / "2026-05-21"
    assert (raw_dir / "trends.jsonl").read_text(encoding="utf-8") == '{"id":"t1"}\n'
    assert not (raw_dir / "notes.txt").exists()


@pytest.mark.unit
def test_materialize_kg_raw_snapshot_returns_none_when_samples_missing(tmp_path: Path) -> None:
    assert materialize_kg_raw_snapshot(tmp_path, snapshot_date=date(2026, 5, 21)) is None


@pytest.mark.unit
def test_materialize_kg_raw_snapshot_returns_none_when_no_jsonl_files(tmp_path: Path) -> None:
    sample_dir = tmp_path / "data" / "samples"
    sample_dir.mkdir(parents=True)
    (sample_dir / "notes.txt").write_text("ignored", encoding="utf-8")

    assert materialize_kg_raw_snapshot(tmp_path, snapshot_date=date(2026, 5, 21)) is None


@pytest.mark.unit
def test_cleanup_dated_files_skips_invalid_date_tokens(tmp_path: Path) -> None:
    invalid_file = tmp_path / "commerce_20261340_summary.json"
    invalid_iso = tmp_path / "2026-99-99-radar.duckdb"
    old_file = tmp_path / "commerce_20260101_summary.json"
    invalid_file.write_text("invalid", encoding="utf-8")
    invalid_iso.write_text("invalid", encoding="utf-8")
    old_file.write_text("old", encoding="utf-8")

    removed = cleanup_dated_files(tmp_path, keep_days=30, today=date(2026, 5, 21))

    assert removed == 1
    assert invalid_file.exists()
    assert invalid_iso.exists()
    assert not old_file.exists()


@pytest.mark.unit
def test_apply_date_storage_policy_materializes_and_prunes(tmp_path: Path) -> None:
    sample_dir = tmp_path / "data" / "samples"
    sample_dir.mkdir(parents=True)
    (sample_dir / "trends.jsonl").write_text('{"id":"t1"}\n', encoding="utf-8")
    raw_old = tmp_path / "data" / "raw" / "2026-01-01"
    raw_old.mkdir(parents=True)
    (raw_old / "old.jsonl").write_text("old", encoding="utf-8")
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    (reports_dir / "commerce_20260101_summary.json").write_text("old", encoding="utf-8")
    daily_dir = tmp_path / "data" / "daily"
    daily_dir.mkdir(parents=True)
    (daily_dir / "2026-01-01-radar.duckdb").write_text("old", encoding="utf-8")
    db_path = tmp_path / "data" / "radar_data.duckdb"
    db_path.write_text("db", encoding="utf-8")

    result = apply_date_storage_policy(
        tmp_path,
        snapshot_db=True,
        keep_raw_days=30,
        keep_report_days=30,
        keep_snapshot_days=30,
        snapshot_date=date(2026, 5, 21),
    )

    assert result["raw_dir_created"] == tmp_path / "data" / "raw" / "2026-05-21"
    assert result["snapshot_path"] == tmp_path / "data" / "daily" / "2026-05-21" / "radar_data.duckdb"
    assert result["raw_pruned"] == 1
    assert result["report_pruned"] == 1
    assert result["snapshot_pruned"] == 1
    assert not raw_old.exists()
    assert not (reports_dir / "commerce_20260101_summary.json").exists()
