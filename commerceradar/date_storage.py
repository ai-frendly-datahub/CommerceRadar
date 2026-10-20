"""CommerceRadar date-partitioned storage.

The daily collector writes public-source articles under `data/raw/<YYYY-MM-DD>/`.
KG sample JSONL stays in `data/samples/` and is not copied into the raw log.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from radar_core.date_storage import (
    cleanup_date_directories,
    snapshot_database,
)
from radar_core.raw_logger import RawLogger  # noqa: F401  (contract surface)

logger = logging.getLogger(__name__)


def materialize_kg_raw_snapshot(
    project_root: Path,
    *,
    snapshot_date: date | None = None,
) -> Path | None:
    """Do not copy KG sample JSONL into the dated raw log.

    ``data/samples/*.jsonl`` remains in the repository for tests and match
    cards. Collection runs must not republish those rows as fresh raw data.
    The arguments are kept so existing callers stay compatible.
    """
    del project_root, snapshot_date
    return None


def _parse_date_token(value: str) -> date | None:
    for match in re.finditer(r"\d{4}-\d{2}-\d{2}|\d{8}", value):
        token = match.group(0)
        if len(token) == 8:
            try:
                return datetime.strptime(token, "%Y%m%d").date()
            except ValueError:
                continue
        try:
            return date.fromisoformat(token)
        except ValueError:
            continue
    return None


def _compact_database(database_path: Path) -> dict[str, object]:
    """Shrink ``database_path`` before it is copied or committed.

    Compaction failure must not block the report or the snapshot. The file
    already on disk is left in place. ``RADAR_DUCKDB_MAX_BYTES`` and
    ``RADAR_DUCKDB_COMPACT=0`` are read inside ``compact_duckdb_file``.
    The default budget is 90 MiB.
    """
    bytes_now = database_path.stat().st_size if database_path.exists() else 0
    fallback: dict[str, object] = {
        "compacted": False,
        "reason": "missing" if not database_path.exists() else "skipped",
        "bytes": bytes_now,
        "bytes_before": bytes_now,
        "rows_deleted": 0,
    }
    if not database_path.exists():
        return fallback
    try:
        from radar_core.db_compact import compact_duckdb_file
    except ImportError as exc:
        logger.warning("duckdb_compact_unavailable path=%s error=%s", database_path, exc)
        fallback["reason"] = "unavailable"
        return fallback
    try:
        result = compact_duckdb_file(database_path)
    except Exception as exc:
        logger.warning("duckdb_compact_failed path=%s error=%s", database_path, exc)
        fallback["reason"] = "failed"
        fallback["bytes"] = database_path.stat().st_size if database_path.exists() else 0
        return fallback
    if isinstance(result, dict):
        return result
    fallback["reason"] = "invalid_result"
    return fallback


def cleanup_dated_files(path: Path, *, keep_days: int, today: date | None = None) -> int:
    if not path.exists() or keep_days < 0:
        return 0
    cutoff = (today or datetime.now(UTC).date()) - timedelta(days=keep_days)
    removed = 0
    for item in path.iterdir():
        if not item.is_file():
            continue
        item_date = _parse_date_token(item.name)
        if item_date is None or item_date >= cutoff:
            continue
        item.unlink()
        removed += 1
    return removed


def apply_date_storage_policy(
    project_root: Path,
    *,
    snapshot_db: bool = False,
    keep_raw_days: int = 90,
    keep_report_days: int = 90,
    keep_snapshot_days: int = 30,
    snapshot_date: date | None = None,
) -> dict[str, object]:
    """Run radar-core retention. Sample JSONL is not copied into ``data/raw``."""
    raw_dir = materialize_kg_raw_snapshot(project_root, snapshot_date=snapshot_date)
    database_path = project_root / "data" / "radar_data.duckdb"
    raw_data_dir = project_root / "data" / "raw"
    report_dir = project_root / "reports"
    snapshot_dir = project_root / "data" / "daily"
    # Compact first so the snapshot is a copy of the file that will be committed.
    compact = _compact_database(database_path)
    snapshot_path: Path | None = None
    if snapshot_db and database_path.exists():
        snapshot_path = snapshot_database(
            database_path,
            snapshot_date=snapshot_date,
            snapshot_root=project_root / "data" / "daily",
        )
    raw_pruned = cleanup_date_directories(raw_data_dir, keep_days=keep_raw_days, today=snapshot_date)
    report_pruned = cleanup_dated_files(report_dir, keep_days=keep_report_days, today=snapshot_date)
    snapshot_pruned = cleanup_dated_files(snapshot_dir, keep_days=keep_snapshot_days, today=snapshot_date)
    return {
        "raw_dir_created": raw_dir,
        "snapshot_path": snapshot_path,
        "raw_pruned": raw_pruned,
        "report_pruned": report_pruned,
        "snapshot_pruned": snapshot_pruned,
        "duckdb_compact": compact,
    }


__all__ = [
    "apply_date_storage_policy",
    "cleanup_dated_files",
    "cleanup_date_directories",
    "materialize_kg_raw_snapshot",
    "snapshot_database",
]
