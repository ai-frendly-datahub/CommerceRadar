"""Collect CommerceRadar articles from local KG sample data.

CommerceRadar's "sources" are local JSONL files (trends, manufacturers, etc.)
rather than network feeds. The collector turns each `Trend` row into an
`Article` for downstream standard processing.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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


def _dedupe_jsonl_by_link(path: Path) -> int:
    """Rewrite a raw article JSONL file with one latest record per link."""
    if not path.exists():
        return 0
    records: list[dict[str, Any]] = []
    index_by_link: dict[str, int] = {}
    duplicates = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            link = str(record.get("link") or "")
            if link and link in index_by_link:
                duplicates += 1
                records[index_by_link[link]] = record
                continue
            if link:
                index_by_link[link] = len(records)
            records.append(record)
    if duplicates:
        with path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return duplicates


def _parse_source_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _source_observed_at(source_meta: dict[str, Any]) -> str | None:
    observed = source_meta.get("verified_at") or source_meta.get("collected_at")
    return str(observed) if observed else None


def _trend_extraction_quality(trend: dict[str, Any], link: str) -> float:
    source_meta = trend.get("source") or {}
    checks = [
        (15, bool(trend.get("id"))),
        (15, bool(link)),
        (15, bool(trend.get("countries"))),
        (15, bool(trend.get("channels"))),
        (15, bool(trend.get("related_categories"))),
        (10, bool(trend.get("keywords"))),
        (10, bool(_source_observed_at(source_meta))),
        (5, bool(source_meta.get("source_type"))),
    ]
    return float(sum(weight for weight, passed in checks if passed))


def _trend_to_article(trend: dict, category: str) -> Article:
    source_meta = trend.get("source") or {}
    source_urls = source_meta.get("source_urls") or []
    link = source_urls[0] if source_urls else f"local://commerce/trend/{trend.get('id', 'unknown')}"
    observed_at = _source_observed_at(source_meta)
    published = _parse_source_datetime(observed_at) or datetime.now(UTC)
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
        published=published,
        source=str(source_meta.get("source_type", "sample_trend")),
        category=category,
        matched_entities=matched_entities,
        collected_at=datetime.now(UTC),
        ontology={
            "kg_entity": {"type": "Trend", "id": str(trend.get("id") or "")},
            "trend": {
                "countries": list(trend.get("countries") or []),
                "channels": list(trend.get("channels") or []),
                "keywords": list(trend.get("keywords") or []),
                "related_categories": list(trend.get("related_categories") or []),
                "signal_strength": trend.get("signal_strength"),
                "seasonality": trend.get("seasonality"),
            },
            "source_meta": {
                "source_type": source_meta.get("source_type"),
                "confidence_level": source_meta.get("confidence_level"),
                "collected_at": source_meta.get("collected_at"),
                "verified_at": source_meta.get("verified_at"),
                "source_urls": list(source_urls),
            },
            "extraction": {
                "quality_score": _trend_extraction_quality(trend, link),
                "observed_at": observed_at,
            },
        },
    )


def collect_sources(
    config: CategoryConfig,
    *,
    project_root: Path | None = None,
    log_raw: bool = True,
) -> list[Article]:
    """Load Trend rows from `data/samples/trends.jsonl` and emit Articles.

    When `log_raw` is True the collected Trends are also logged via
    `radar_core.raw_logger.RawLogger` to `data/raw/<YYYY-MM-DD>/` so the
    standard `raw_data_by_date` contract sees a fresh dated record each run.
    """
    root = project_root if project_root is not None else _project_root()
    trends_path = root / "data" / "samples" / "trends.jsonl"
    rows = _read_jsonl(trends_path)
    articles = [_trend_to_article(row, config.category_name) for row in rows]

    if log_raw and articles:
        from radar_core.raw_logger import RawLogger

        raw_dir = root / "data" / "raw"
        raw_logger = RawLogger(raw_dir)
        output_path = raw_logger.log(articles, source_name="commerce_kg_trends")
        _dedupe_jsonl_by_link(output_path)

    return articles
