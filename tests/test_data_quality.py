from datetime import date

from flomers_kg.data_quality import (
    completeness_score,
    compute_quality_score,
    freshness_score,
)


def test_freshness_score_handles_iso_datetime_and_future_dates():
    assert freshness_score("2026-05-20T12:34:56Z", today=date(2026, 5, 21)) > 19
    assert freshness_score("2026-05-22", today=date(2026, 5, 21)) == 20
    assert freshness_score("not-a-date", today=date(2026, 5, 21)) == 0
    assert freshness_score(None, today=date(2026, 5, 21)) == 0


def test_completeness_score_treats_empty_values_as_missing():
    score = completeness_score(
        {"name": "ABC", "website": "", "tags": [], "meta": {}, "country": "KR"},
        required_fields=["name", "website", "tags", "meta", "country"],
    )

    assert score == 10.0
    assert completeness_score({}, []) == 25.0


def test_compute_quality_score_clamps_inputs_and_reports_warnings():
    result = compute_quality_score(
        {"name": ""},
        required_fields=["name", "website"],
        source_confidence=2.0,
        observed_at="bad-date",
        entity_resolution_confidence=-1.0,
        conflict_count=10,
        today=date(2026, 5, 21),
    )

    assert result.source_confidence == 25.0
    assert result.entity_resolution_confidence == 0.0
    assert result.conflict_penalty == 20.0
    assert result.score == 5.0
    assert "필수 필드 완성도가 낮습니다." in result.warnings
    assert "데이터 최신성이 낮습니다." in result.warnings
    assert "충돌 데이터가 존재합니다." in result.warnings


def test_compute_quality_score_warns_on_low_source_confidence():
    result = compute_quality_score(
        {"name": "ABC"},
        required_fields=["name"],
        source_confidence=0.1,
        observed_at="2026-05-21",
        today=date(2026, 5, 21),
    )

    assert "출처 신뢰도가 낮습니다." in result.warnings
