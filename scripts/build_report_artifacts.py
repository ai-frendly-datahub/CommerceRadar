from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from flomers_kg.reporting import write_report_artifacts


def main() -> int:
    paths = write_report_artifacts(ROOT)
    for label, path in paths.items():
        print(f"{label}: {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
