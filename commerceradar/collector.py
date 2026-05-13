"""Collect CommerceRadar articles from local KG sample data.

CommerceRadar's "sources" are local JSONL files (trends, manufacturers, etc.)
rather than network feeds. The collector turns each `Trend` row into an
`Article` for downstream standard processing.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from .models import Article, CategoryConfig


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _trend_to_article(trend: dict, category: str) -> Article:
    source_meta = trend.get("source") or {}
    source_urls = source_meta.get("source_urls") or []
    link = source_urls[0] if source_urls else f"local://commerce/trend/{trend.get('id', 'unknown')}"
    matched_entities: dict[str, list[str]] = {}
    if trend.get("countries"):
        matched_entities["Country"] = list(trend["countries"])
    if trend.get("channels"):
        matched_entities["Channel"] = list(trend["channels"])
    if trend.get("related_categories"):
        matched_entities["Category"] = list(trend["related_categories"])

    return Article(
        title=str(trend.get("name", "Untitled trend")),
        link=link,
        summary=", ".join(trend.get("keywords") or []),
        published=datetime.now(UTC),
        source=str(source_meta.get("source_type", "sample_trend")),
        category=category,
        matched_entities=matched_entities,
        collected_at=datetime.now(UTC),
    )


def collect_sources(
    config: CategoryConfig,
    *,
    project_root: Path | None = None,
) -> list[Article]:
    """Load Trend rows from `data/samples/trends.jsonl` and emit Articles."""
    root = project_root if project_root is not None else _project_root()
    trends_path = root / "data" / "samples" / "trends.jsonl"
    rows = _read_jsonl(trends_path)
    return [_trend_to_article(row, config.category_name) for row in rows]
