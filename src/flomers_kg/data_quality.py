from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class QualityResult:
    score: float
    completeness: float
    source_confidence: float
    freshness: float
    entity_resolution_confidence: float
    operator_verification: float
    conflict_penalty: float
    warnings: list[str]


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


def freshness_score(observed_at: str | None, max_age_days: int = 90, today: date | None = None) -> float:
    """Return 0-20 freshness score."""
    observed = _parse_date(observed_at)
    if observed is None:
        return 0.0
    today = today or date.today()
    age = max(0, (today - observed).days)
    if age >= max_age_days:
        return 0.0
    return round(20 * (1 - age / max_age_days), 2)


def completeness_score(record: dict[str, Any], required_fields: list[str]) -> float:
    if not required_fields:
        return 25.0
    present = 0
    for field in required_fields:
        value = record.get(field)
        if value not in (None, "", [], {}):
            present += 1
    return round(25 * present / len(required_fields), 2)


def compute_quality_score(
    record: dict[str, Any],
    required_fields: list[str],
    source_confidence: float = 0.35,
    observed_at: str | None = None,
    entity_resolution_confidence: float = 0.5,
    operator_verified: bool = False,
    conflict_count: int = 0,
    max_age_days: int = 90,
    today: date | None = None,
) -> QualityResult:
    warnings: list[str] = []
    completeness = completeness_score(record, required_fields)
    source = round(25 * min(1.0, max(0.0, source_confidence)), 2)
    freshness = freshness_score(observed_at, max_age_days=max_age_days, today=today)
    entity = round(15 * min(1.0, max(0.0, entity_resolution_confidence)), 2)
    operator = 15.0 if operator_verified else 0.0
    conflict_penalty = min(20.0, conflict_count * 5.0)

    if completeness < 18:
        warnings.append("필수 필드 완성도가 낮습니다.")
    if source < 12:
        warnings.append("출처 신뢰도가 낮습니다.")
    if freshness < 8:
        warnings.append("데이터 최신성이 낮습니다.")
    if conflict_penalty:
        warnings.append("충돌 데이터가 존재합니다.")

    total = max(0.0, round(completeness + source + freshness + entity + operator - conflict_penalty, 2))
    return QualityResult(
        score=total,
        completeness=completeness,
        source_confidence=source,
        freshness=freshness,
        entity_resolution_confidence=entity,
        operator_verification=operator,
        conflict_penalty=conflict_penalty,
        warnings=warnings,
    )
