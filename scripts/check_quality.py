"""CommerceRadar quality check script — standard Radar contract."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = PROJECT_ROOT.parent
RADAR_CORE_ROOT = WORKSPACE_ROOT / "radar-core"
if RADAR_CORE_ROOT.exists():
    sys.path.insert(0, str(RADAR_CORE_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))


def generate_quality_artifacts(project_root: Path) -> dict[str, Path]:
    from commerceradar.quality_report import write_quality_report

    quality_path = write_quality_report(project_root)
    return {"quality": quality_path}


def main() -> int:
    paths = generate_quality_artifacts(PROJECT_ROOT)
    for label, path in paths.items():
        print(f"{label}: {path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
