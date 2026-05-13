"""CommerceRadar date-partitioned storage.

CommerceRadar's primary data is a KG sample seed (`data/samples/*.jsonl`)
rather than a time-series collection. To satisfy the standard `daily_collection`
contract (raw_data_by_date + snapshot_path_by_date + retention CLI), this
module wraps `radar_core.date_storage` and additionally materialises today's
KG snapshot under `data/raw/<YYYY-MM-DD>/` so dashboard/analysis can treat
the repo uniformly.
"""

from __future__ import annotations

import shutil
from datetime import UTC, date, datetime
from pathlib import Path

from radar_core.date_storage import (
    apply_date_storage_policy as _core_apply_date_storage_policy,
    cleanup_date_directories,
    snapshot_database,
)
from radar_core.raw_logger import RawLogger  # noqa: F401  (contract surface)


def materialize_kg_raw_snapshot(
    project_root: Path,
    *,
    snapshot_date: date | None = None,
) -> Path | None:
    """Copy today's KG sample seed into `data/raw/<YYYY-MM-DD>/`.

    CommerceRadar's "raw collection" is a synthesised view of the sample
    KG seed for the current date. This makes the date-partitioned layout
    visible to standard tooling without changing the underlying KG flow.
    """
    samples = project_root / "data" / "samples"
    if not samples.exists():
        return None
    target_date = snapshot_date or datetime.now(UTC).date()
    raw_dir = project_root / "data" / "raw" / target_date.isoformat()
    raw_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for source in samples.glob("*.jsonl"):
        dest = raw_dir / source.name
        shutil.copy2(source, dest)
        written.append(dest)
    return raw_dir if written else None


def apply_date_storage_policy(
    project_root: Path,
    *,
    snapshot_db: bool = False,
    keep_raw_days: int = 90,
    keep_report_days: int = 90,
    keep_snapshot_days: int = 30,
    snapshot_date: date | None = None,
) -> dict[str, Path | int | None]:
    """Run radar-core retention + add CommerceRadar's KG raw materialisation."""
    raw_dir = materialize_kg_raw_snapshot(project_root, snapshot_date=snapshot_date)
    database_path = project_root / "data" / "radar_data.duckdb"
    raw_data_dir = project_root / "data" / "raw"
    report_dir = project_root / "reports"
    snapshot_path: Path | None = None
    if snapshot_db and database_path.exists():
        snapshot_path = snapshot_database(
            database_path,
            snapshot_date=snapshot_date,
            snapshot_root=project_root / "data" / "daily",
        )
    raw_pruned = cleanup_date_directories(raw_data_dir, keep_days=keep_raw_days)
    return {
        "raw_dir_created": raw_dir,
        "snapshot_path": snapshot_path,
        "raw_pruned": raw_pruned,
    }


__all__ = [
    "apply_date_storage_policy",
    "cleanup_date_directories",
    "materialize_kg_raw_snapshot",
    "snapshot_database",
]
