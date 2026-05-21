"""Minimal quality report for CommerceRadar.

Reads the latest `commerce_<date>_summary.json` and produces a quality
summary in `reports/commerce_<date>_quality.json` matching the standard shape
that `radar-analysis` and `radar-dashboard` expect.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


SAMPLE_SCHEMA_PAIRS = {
    "manufacturers": ("manufacturers.jsonl", "manufacturer.schema.json"),
    "products": ("products.jsonl", "product.schema.json"),
    "distributors": ("distributors.jsonl", "distributor.schema.json"),
    "sellers": ("sellers.jsonl", "seller.schema.json"),
    "trends": ("trends.jsonl", "trend.schema.json"),
    "evidence": ("evidence_records.jsonl", "evidence.schema.json"),
    "transactions": ("transactions.jsonl", "transaction_result.schema.json"),
}

SAMPLE_REQUIRED_FIELDS = {
    "manufacturers": ["id", "name", "country", "categories", "source"],
    "products": ["id", "manufacturer_id", "name", "category", "keywords", "suitable_channels", "source"],
    "distributors": ["id", "name", "country", "portfolio_categories", "distribution_channels", "source"],
    "sellers": ["id", "name", "country", "channels", "categories", "source"],
    "trends": ["id", "name", "countries", "channels", "keywords", "related_categories", "source"],
    "evidence": ["id", "source_type", "source_urls", "confidence", "observed_at", "related_entities"],
    "transactions": ["id", "match_id", "status", "started_at", "metrics"],
}

QUALITY_WARNING_THRESHOLD = 70.0
EVIDENCE_EXPIRY_WARNING_DAYS = 14


def _latest_summary(reports_dir: Path) -> Path | None:
    summaries = sorted(reports_dir.glob("commerce_*_summary.json"))
    return summaries[-1] if summaries else None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line"] = line_no
            rows.append(row)
    return rows


def _source_observed_at(row: dict[str, Any]) -> str | None:
    source = row.get("source") or {}
    if not isinstance(source, dict):
        return None
    observed = source.get("verified_at") or source.get("collected_at")
    return str(observed) if observed else None


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(str(value)[:10])
        except ValueError:
            return None


def _freshness_score(observed_at: str | None, *, today: date, max_age_days: int = 90) -> float:
    observed = _parse_date(observed_at)
    if observed is None:
        return 0.0
    age = max(0, (today - observed).days)
    if age >= max_age_days:
        return 0.0
    return round(20 * (1 - age / max_age_days), 2)


def _completeness_score(row: dict[str, Any], required_fields: list[str]) -> float:
    if not required_fields:
        return 25.0
    present = sum(1 for field in required_fields if row.get(field) not in (None, "", [], {}))
    return round(25 * present / len(required_fields), 2)


def _source_confidence(row: dict[str, Any], kind: str) -> float:
    if kind == "evidence":
        return min(1.0, max(0.0, float(row.get("confidence") or 0.0)))
    if kind == "transactions":
        return 0.95
    source = row.get("source") or {}
    if not isinstance(source, dict):
        return 0.0
    return min(1.0, max(0.0, float(source.get("confidence_level") or 0.0) / 7.0))


def _observed_at(row: dict[str, Any], kind: str) -> str | None:
    if kind == "evidence":
        observed = row.get("observed_at")
        return str(observed) if observed else None
    if kind == "transactions":
        observed = row.get("started_at")
        return str(observed) if observed else None
    return _source_observed_at(row)


def _quality_score(row: dict[str, Any], kind: str, *, today: date) -> float:
    required = SAMPLE_REQUIRED_FIELDS.get(kind, [])
    completeness = _completeness_score(row, required)
    source = round(25 * _source_confidence(row, kind), 2)
    freshness = _freshness_score(_observed_at(row, kind), today=today)
    entity_resolution = 12.0
    return max(0.0, round(completeness + source + freshness + entity_resolution, 2))


def _sample_quality_scores(project_root: Path, *, today: date) -> dict[str, Any]:
    sample_dir = project_root / "data" / "samples"
    averages: dict[str, float] = {}
    minimums: dict[str, float] = {}
    low_quality_groups: list[dict[str, Any]] = []

    for kind, (data_name, _) in SAMPLE_SCHEMA_PAIRS.items():
        scores = [
            _quality_score({key: value for key, value in row.items() if not key.startswith("_")}, kind, today=today)
            for row in _read_jsonl(sample_dir / data_name)
        ]
        if not scores:
            continue
        avg = round(sum(scores) / len(scores), 2)
        min_score = round(min(scores), 2)
        averages[kind] = avg
        minimums[kind] = min_score
        if avg < QUALITY_WARNING_THRESHOLD:
            low_quality_groups.append({"kind": kind, "average_score": avg})

    return {
        "average_quality_by_kind": averages,
        "minimum_quality_by_kind": minimums,
        "low_quality_group_count": len(low_quality_groups),
        "low_quality_groups": low_quality_groups,
    }


def _evidence_validity_checks(project_root: Path, *, today: date) -> dict[str, Any]:
    expiring: list[str] = []
    expired: list[str] = []
    for row in _read_jsonl(project_root / "data" / "samples" / "evidence_records.jsonl"):
        valid_until = _parse_date(row.get("valid_until"))
        if valid_until is None:
            continue
        days_left = (valid_until - today).days
        if days_left < 0:
            expired.append(str(row.get("id")))
        elif days_left <= EVIDENCE_EXPIRY_WARNING_DAYS:
            expiring.append(str(row.get("id")))
    return {
        "evidence_expiring_soon_count": len(expiring),
        "evidence_expiring_soon_ids": sorted(expiring),
        "evidence_expired_count": len(expired),
        "evidence_expired_ids": sorted(expired),
    }


def _validate_sample_data(project_root: Path) -> dict[str, Any]:
    sample_dir = project_root / "data" / "samples"
    schema_dir = project_root / "schemas"
    row_counts: dict[str, int] = {}
    schema_errors: list[str] = []
    duplicate_ids: list[str] = []
    missing_source_dates: list[str] = []

    for kind, (data_name, schema_name) in SAMPLE_SCHEMA_PAIRS.items():
        rows = _read_jsonl(sample_dir / data_name)
        row_counts[kind] = len(rows)
        schema_path = schema_dir / schema_name
        if schema_path.exists():
            validator = Draft202012Validator(json.loads(schema_path.read_text(encoding="utf-8")))
            for row in rows:
                public_row = {key: value for key, value in row.items() if not key.startswith("_")}
                for error in validator.iter_errors(public_row):
                    schema_errors.append(f"{data_name}:{row.get('_line')}: {error.message}")
        id_counts = Counter(str(row.get("id")) for row in rows if row.get("id"))
        duplicate_ids.extend(f"{kind}:{entity_id}" for entity_id, count in id_counts.items() if count > 1)
        if kind not in {"evidence", "transactions"}:
            missing_source_dates.extend(
                f"{kind}:{row.get('id')}" for row in rows if not _source_observed_at(row)
            )

    return {
        "row_counts": row_counts,
        "schema_error_count": len(schema_errors),
        "schema_errors": schema_errors[:20],
        "duplicate_id_count": len(duplicate_ids),
        "duplicate_ids": sorted(duplicate_ids),
        "missing_source_date_count": len(missing_source_dates),
        "missing_source_dates": sorted(missing_source_dates),
    }


def _reference_checks(project_root: Path) -> dict[str, Any]:
    sample_dir = project_root / "data" / "samples"
    manufacturers = _read_jsonl(sample_dir / "manufacturers.jsonl")
    products = _read_jsonl(sample_dir / "products.jsonl")
    distributors = _read_jsonl(sample_dir / "distributors.jsonl")
    sellers = _read_jsonl(sample_dir / "sellers.jsonl")
    trends = _read_jsonl(sample_dir / "trends.jsonl")
    evidence_rows = _read_jsonl(sample_dir / "evidence_records.jsonl")
    transactions = _read_jsonl(sample_dir / "transactions.jsonl")

    manufacturer_ids = {row.get("id") for row in manufacturers}
    product_ids = {row.get("id") for row in products}
    distributor_ids = {row.get("id") for row in distributors}
    seller_ids = {row.get("id") for row in sellers}
    entity_ids = manufacturer_ids | product_ids | distributor_ids | seller_ids | {row.get("id") for row in trends}

    missing: list[str] = []
    for product in products:
        if product.get("manufacturer_id") not in manufacturer_ids:
            missing.append(f"product_manufacturer:{product.get('id')}->{product.get('manufacturer_id')}")
    for evidence in evidence_rows:
        for entity_id in evidence.get("related_entities") or []:
            if entity_id not in entity_ids:
                missing.append(f"evidence_entity:{evidence.get('id')}->{entity_id}")
    for transaction in transactions:
        parts = str(transaction.get("match_id") or "").split("::")
        if len(parts) != 5:
            missing.append(f"transaction_match_format:{transaction.get('id')}")
            continue
        _, manufacturer_id, product_id, distributor_id, seller_id = parts
        if manufacturer_id not in manufacturer_ids:
            missing.append(f"transaction_manufacturer:{transaction.get('id')}->{manufacturer_id}")
        if product_id not in product_ids:
            missing.append(f"transaction_product:{transaction.get('id')}->{product_id}")
        if distributor_id not in distributor_ids:
            missing.append(f"transaction_distributor:{transaction.get('id')}->{distributor_id}")
        if seller_id not in seller_ids:
            missing.append(f"transaction_seller:{transaction.get('id')}->{seller_id}")

    return {"reference_error_count": len(missing), "reference_errors": sorted(missing)}


def _latest_raw_trend_log(project_root: Path) -> Path | None:
    raw_root = project_root / "data" / "raw"
    candidates = sorted(raw_root.glob("*/commerce_kg_trends.jsonl"))
    return candidates[-1] if candidates else None


def _raw_duplicate_checks(project_root: Path) -> dict[str, Any]:
    path = _latest_raw_trend_log(project_root)
    if path is None:
        return {
            "raw_trend_log": None,
            "raw_trend_rows": 0,
            "raw_trend_duplicate_link_count": 0,
            "raw_trend_missing_kg_id_count": 0,
            "raw_trend_missing_entity_count": 0,
            "raw_trend_missing_source_observed_at_count": 0,
            "raw_trend_average_extraction_quality": 0.0,
        }
    rows = _read_jsonl(path)
    links = [str(row.get("link")) for row in rows if row.get("link")]
    duplicate_count = sum(count - 1 for count in Counter(links).values() if count > 1)
    quality_scores = [_raw_trend_extraction_quality(row) for row in rows]
    return {
        "raw_trend_log": str(path.relative_to(project_root)),
        "raw_trend_rows": len(rows),
        "raw_trend_duplicate_link_count": duplicate_count,
        "raw_trend_missing_kg_id_count": sum(1 for row in rows if not _raw_trend_kg_id(row)),
        "raw_trend_missing_entity_count": sum(1 for row in rows if not _raw_trend_entities_complete(row)),
        "raw_trend_missing_source_observed_at_count": sum(
            1 for row in rows if not _raw_trend_source_observed_at(row)
        ),
        "raw_trend_average_extraction_quality": round(sum(quality_scores) / len(quality_scores), 2)
        if quality_scores
        else 0.0,
    }


def _raw_trend_kg_id(row: dict[str, Any]) -> str | None:
    ontology = row.get("ontology") or {}
    if not isinstance(ontology, dict):
        return None
    kg_entity = ontology.get("kg_entity") or {}
    if not isinstance(kg_entity, dict):
        return None
    trend_id = kg_entity.get("id")
    return str(trend_id) if trend_id else None


def _raw_trend_source_observed_at(row: dict[str, Any]) -> str | None:
    ontology = row.get("ontology") or {}
    if not isinstance(ontology, dict):
        return None
    extraction = ontology.get("extraction") or {}
    if isinstance(extraction, dict) and extraction.get("observed_at"):
        return str(extraction["observed_at"])
    source_meta = ontology.get("source_meta") or {}
    if not isinstance(source_meta, dict):
        return None
    observed = source_meta.get("verified_at") or source_meta.get("collected_at")
    return str(observed) if observed else None


def _raw_trend_entities_complete(row: dict[str, Any]) -> bool:
    entities = row.get("matched_entities") or {}
    if not isinstance(entities, dict):
        return False
    required = ("Country", "Channel", "Category")
    return all(bool(entities.get(name)) for name in required)


def _raw_trend_extraction_quality(row: dict[str, Any]) -> float:
    ontology = row.get("ontology") or {}
    if isinstance(ontology, dict):
        extraction = ontology.get("extraction") or {}
        if isinstance(extraction, dict) and isinstance(extraction.get("quality_score"), (int, float)):
            return max(0.0, min(100.0, float(extraction["quality_score"])))

    checks = [
        (20, bool(row.get("title"))),
        (20, bool(row.get("link"))),
        (20, bool(row.get("summary"))),
        (20, _raw_trend_entities_complete(row)),
        (10, bool(row.get("published"))),
        (10, bool(row.get("source"))),
    ]
    return float(sum(weight for weight, passed in checks if passed))


def _data_quality_checks(project_root: Path) -> dict[str, Any]:
    today = datetime.now(UTC).date()
    sample_checks = _validate_sample_data(project_root)
    reference_checks = _reference_checks(project_root)
    raw_checks = _raw_duplicate_checks(project_root)
    quality_scores = _sample_quality_scores(project_root, today=today)
    evidence_validity = _evidence_validity_checks(project_root, today=today)
    return {**sample_checks, **reference_checks, **raw_checks, **quality_scores, **evidence_validity}


def build_quality_report(project_root: Path) -> dict[str, Any]:
    reports_dir = project_root / "reports"
    summary_path = _latest_summary(reports_dir)
    data_quality_checks = _data_quality_checks(project_root)
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
            "data_quality_checks": data_quality_checks,
        }
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    sources = summary.get("sources") or {}
    collected_source_count = int(summary.get("collected_source_count") or len(sources))
    warnings = list(summary.get("warnings") or [])
    if data_quality_checks["schema_error_count"]:
        warnings.append("sample schema validation errors exist")
    if data_quality_checks["duplicate_id_count"]:
        warnings.append("duplicate sample ids exist")
    if data_quality_checks["reference_error_count"]:
        warnings.append("sample reference integrity errors exist")
    if data_quality_checks["missing_source_date_count"]:
        warnings.append("sample source dates are missing")
    if data_quality_checks["raw_trend_duplicate_link_count"]:
        warnings.append("raw trend log contains duplicate links")
    if data_quality_checks["raw_trend_missing_kg_id_count"]:
        warnings.append("raw trend log is missing KG trend ids")
    if data_quality_checks["raw_trend_missing_entity_count"]:
        warnings.append("raw trend log is missing matched entities")
    if data_quality_checks["raw_trend_missing_source_observed_at_count"]:
        warnings.append("raw trend log is missing source observed dates")
    if (
        data_quality_checks["raw_trend_rows"]
        and data_quality_checks["raw_trend_average_extraction_quality"] < QUALITY_WARNING_THRESHOLD
    ):
        warnings.append("raw trend extraction quality below threshold")
    if data_quality_checks["low_quality_group_count"]:
        warnings.append("sample quality score below threshold")
    if data_quality_checks["evidence_expiring_soon_count"] or data_quality_checks["evidence_expired_count"]:
        warnings.append("evidence records are expired or expiring soon")
    if int(summary.get("pending_evidence_count") or 0):
        warnings.append("match candidates have pending evidence")
    return {
        "category": "commerce",
        "generated_at": datetime.now(UTC).isoformat(),
        "sources_enabled": int(summary.get("source_count") or 0),
        "sources_fresh": collected_source_count,
        "collection_errors": 0,
        "controlled_rollout": {"required": 0, "passed": 0},
        "daily_review_items": int(summary.get("article_count") or 0)
        - int(summary.get("matched_count") or 0),
        "pending_evidence_items": int(summary.get("pending_evidence_count") or 0),
        "warnings": warnings,
        "summary_file": summary_path.name,
        "data_quality_checks": data_quality_checks,
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
