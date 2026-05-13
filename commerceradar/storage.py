"""CommerceRadar storage — minimal RadarStorage subclass.

The KG report builder (`flomers_kg.reporting`) is stateless and writes directly
to `reports/`. This storage class exists so the standard tooling
(`tests/unit/test_check_quality_script.py`, `radar_core.RadarStorage` daily
snapshot policy) can operate uniformly. Daily snapshots are local-only and not
required by the KG pipeline.
"""

from __future__ import annotations

from pathlib import Path

from radar_core.storage import RadarStorage as _RadarStorageBase


class RadarStorage(_RadarStorageBase):
    """CommerceRadar storage with no-op daily-snapshot policy."""

    def create_daily_snapshot(self, *args, **kwargs) -> Path | None:  # noqa: D401
        try:
            return super().create_daily_snapshot(*args, **kwargs)
        except Exception:
            return None

    def cleanup_old_snapshots(self, *args, **kwargs) -> int:
        try:
            return super().cleanup_old_snapshots(*args, **kwargs)
        except Exception:
            return 0


__all__ = ["RadarStorage"]
