"""CommerceRadar orchestrator — standard Radar entry point.

Pipeline: load category config -> collect Articles from KG samples ->
apply entity rules -> generate report -> write quality report.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = PROJECT_ROOT.parent
RADAR_CORE_ROOT = WORKSPACE_ROOT / "radar-core"
if RADAR_CORE_ROOT.exists():
    sys.path.insert(0, str(RADAR_CORE_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run CommerceRadar daily pipeline.")
    parser.add_argument("--category", default="commerce")
    parser.add_argument("--snapshot-db", action="store_true", help="Copy radar_data.duckdb into data/daily/<date>/")
    parser.add_argument("--keep-days", type=int, default=90, help="Retain DB snapshots up to N days")
    parser.add_argument("--keep-raw-days", type=int, default=90, help="Retain data/raw/<date>/ up to N days")
    parser.add_argument("--keep-report-days", type=int, default=90, help="Retain dated report artifacts up to N days")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    from commerceradar.analyzer import apply_entity_rules
    from commerceradar.collector import collect_sources
    from commerceradar.config_loader import load_category_config
    from commerceradar.date_storage import apply_date_storage_policy
    from commerceradar.quality_report import write_quality_report
    from commerceradar.reporter import generate_report

    config = load_category_config(args.category)
    articles = collect_sources(config, project_root=PROJECT_ROOT)
    annotated = apply_entity_rules(articles, config.entities)

    storage_result = apply_date_storage_policy(
        PROJECT_ROOT,
        snapshot_db=args.snapshot_db,
        keep_raw_days=args.keep_raw_days,
        keep_report_days=args.keep_report_days,
        keep_snapshot_days=args.keep_days,
    )
    report_paths = generate_report(project_root=PROJECT_ROOT)
    quality_path = write_quality_report(PROJECT_ROOT)

    print(f"category: {config.category_name}")
    print(f"articles (kg trends): {len(annotated)}")
    if storage_result.get("raw_dir_created"):
        print(f"raw_dir: {storage_result['raw_dir_created'].relative_to(PROJECT_ROOT)}")
    if storage_result.get("snapshot_path"):
        print(f"snapshot: {storage_result['snapshot_path'].relative_to(PROJECT_ROOT)}")
    print(f"raw_pruned: {storage_result.get('raw_pruned', 0)}")
    print(f"report_pruned: {storage_result.get('report_pruned', 0)}")
    print(f"snapshot_pruned: {storage_result.get('snapshot_pruned', 0)}")
    print(f"report: {report_paths['report'].relative_to(PROJECT_ROOT)}")
    print(f"summary: {report_paths['summary'].relative_to(PROJECT_ROOT)}")
    print(f"index: {report_paths['index'].relative_to(PROJECT_ROOT)}")
    print(f"quality: {quality_path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
