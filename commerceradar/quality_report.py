"""Minimal quality report for CommerceRadar.

Reads the latest `commerce_<date>_summary.json` and produces a quality
summary in `reports/commerce_<date>_quality.json` matching the standard shape
that `radar-analysis` and `radar-dashboard` expect.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _latest_summary(reports_dir: Path) -> Path | None:
    summaries = sorted(reports_dir.glob("commerce_*_summary.json"))
    return summaries[-1] if summaries else None


def build_quality_report(project_root: Path) -> dict[str, Any]:
    reports_dir = project_root / "reports"
    summary_path = _latest_summary(reports_dir)
    if summary_path is None:
        return {
            "category": "commerce",
            "generated_at": datetime.now(UTC).isoformat(),
            "sources_enabled": 0,
            "sources_fresh": 0,
            "collection_errors": 0,
            "controlled_rollout": {"required": 0, "passed": 0},
            "daily_review_items": 0,
            "warnings": ["no commerce summary available"],
        }
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    sources = summary.get("sources") or {}
    return {
        "category": "commerce",
        "generated_at": datetime.now(UTC).isoformat(),
        "sources_enabled": int(summary.get("source_count") or 0),
        "sources_fresh": len(sources),
        "collection_errors": 0,
        "controlled_rollout": {"required": 0, "passed": 0},
        "daily_review_items": int(summary.get("article_count") or 0)
        - int(summary.get("matched_count") or 0),
        "warnings": list(summary.get("warnings") or []),
        "summary_file": summary_path.name,
    }


def write_quality_report(project_root: Path) -> Path:
    payload = build_quality_report(project_root)
    reports_dir = project_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    out_path = reports_dir / "commerce_quality.json"
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return out_path


__all__ = ["build_quality_report", "write_quality_report"]
