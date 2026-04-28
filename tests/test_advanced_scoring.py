from datetime import date

from flomers_kg.advanced_scoring import score_advanced_match
from flomers_kg.data_quality import compute_quality_score, freshness_score
from flomers_kg.models import Distributor, Manufacturer, Product, Seller, Trend
from flomers_kg.query_planner import plan_contextual_query


def test_query_planner_extracts_country_and_category():
    plan = plan_contextual_query("일본에서 향·헤어 조합 추천")
    assert "JP" in plan.entities["countries"]
    assert "haircare" in plan.entities["categories"]
    assert plan.intent in {"recommend_combo", "discover_opportunity"}


def test_quality_score_penalizes_old_data():
    assert freshness_score("2026-01-01", max_age_days=100, today=date(2026, 1, 11)) > 15
    assert freshness_score("2025-01-01", max_age_days=100, today=date(2026, 1, 11)) == 0
    result = compute_quality_score(
        {"name": "ABC", "website": "https://example.com"},
        required_fields=["name", "website", "category"],
        source_confidence=0.8,
        observed_at="2026-01-01",
        entity_resolution_confidence=0.9,
        operator_verified=True,
        today=date(2026, 1, 11),
    )
    assert result.score > 70


def test_advanced_score_recommends_strong_sample_combo():
    manufacturer = Manufacturer(
        id="m1",
        name="ABC",
        country="KR",
        categories=["haircare"],
        trust_level=5,
        response_score=4.5,
    )
    product = Product(
        id="p1",
        manufacturer_id="m1",
        name="헤어오일",
        category="haircare",
        keywords=["hair oil", "fragrance", "damaged hair", "gift"],
        suitable_channels=["Instagram", "BASE"],
        suitable_countries=["JP"],
        moq=500,
        cost=3000,
        suggested_price=24000,
        risks=[],
    )
    distributor = Distributor(
        id="d1",
        name="Tokyo D",
        country="JP",
        warehouse_locations=["Saitama"],
        portfolio_categories=["haircare", "beauty"],
        distribution_channels=["Instagram", "BASE"],
        trade_types=["consignment"],
    )
    seller = Seller(
        id="s1",
        name="Tokyo S",
        country="JP",
        channels=["Instagram", "BASE"],
        categories=["haircare", "fragrance"],
        trend_keywords=["hair oil", "fragrance"],
        review_keywords=["damaged hair", "gift"],
        commerce_capabilities=["content_creation", "fulfillment"],
    )
    trend = Trend(
        id="t1",
        name="향 헤어",
        countries=["JP"],
        channels=["Instagram", "BASE"],
        keywords=["hair oil", "fragrance", "damaged hair"],
        related_categories=["haircare"],
        signal_strength=0.9,
    )
    score = score_advanced_match(
        manufacturer,
        product,
        distributor,
        seller,
        [trend],
        target_country="JP",
        target_channels=["Instagram", "BASE"],
        evidence_confidence=0.9,
        market_growth_signal=0.8,
        expected_margin_rate=0.4,
    )
    assert score.total >= 80
    assert score.recommendation in {"추천", "강력 추천"}
