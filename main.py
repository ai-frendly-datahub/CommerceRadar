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
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    from commerceradar.analyzer import apply_entity_rules
    from commerceradar.collector import collect_sources
    from commerceradar.config_loader import load_category_config
    from commerceradar.quality_report import write_quality_report
    from commerceradar.reporter import generate_report

    config = load_category_config(args.category)
    articles = collect_sources(config, project_root=PROJECT_ROOT)
    annotated = apply_entity_rules(articles, config.entities)

    report_paths = generate_report(project_root=PROJECT_ROOT)
    quality_path = write_quality_report(PROJECT_ROOT)

    print(f"category: {config.category_name}")
    print(f"articles (kg trends): {len(annotated)}")
    print(f"report: {report_paths['report'].relative_to(PROJECT_ROOT)}")
    print(f"summary: {report_paths['summary'].relative_to(PROJECT_ROOT)}")
    print(f"index: {report_paths['index'].relative_to(PROJECT_ROOT)}")
    print(f"quality: {quality_path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
