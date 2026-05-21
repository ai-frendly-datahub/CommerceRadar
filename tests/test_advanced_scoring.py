from datetime import date

from flomers_kg.advanced_scoring import score_advanced_match
from flomers_kg.data_quality import compute_quality_score, freshness_score
from flomers_kg.models import Distributor, Manufacturer, Product, Seller, Trend
from flomers_kg.query_planner import plan_contextual_query


def test_query_planner_extracts_country_and_category():
    plan = plan_contextual_query("일본에서 향·헤어 조합 추천")
    assert "JP" in plan.entities["countries"]
    assert "JP" in plan.entities["target_countries"]
    assert "haircare" in plan.entities["categories"]
    assert plan.intent in {"recommend_combo", "discover_opportunity"}


def test_query_planner_separates_source_and_target_country():
    plan = plan_contextual_query("일본에서 향·헤어 트렌드에 맞는 한국 제조사-유통사-판매사 조합 추천")
    assert plan.intent == "recommend_combo"
    assert plan.expected_output == "combo_cards"
    assert plan.entities["target_countries"] == ["JP"]
    assert plan.entities["source_countries"] == ["KR"]
    assert plan.entities["countries"] == ["JP", "KR"]


def test_query_planner_covers_intent_branches_and_channel_extraction():
    failure = plan_contextual_query("일본 BASE 테스트는 왜 실패했나")
    assert failure.intent == "analyze_failure"
    assert failure.expected_output == "failure_analysis"
    assert failure.entities["channels"] == ["BASE"]

    company = plan_contextual_query("일본 뷰티 유통사 찾아")
    assert company.intent == "find_company"
    assert company.expected_output == "company_list"

    evaluation = plan_contextual_query("이 헤어 제품이 일본 시장에 적합한지 판단")
    assert evaluation.intent == "evaluate_product"
    assert evaluation.expected_output == "product_fit_report"

    opportunity = plan_contextual_query("중국 펫 틈새 트렌드")
    assert opportunity.intent == "discover_opportunity"
    assert opportunity.expected_output == "opportunity_report"

    default = plan_contextual_query("향 제품")
    assert default.intent == "recommend_combo"
    assert default.entities["target_countries"] == []
    assert "대상 국가가 명확하지 않으므로 KR/JP/CN 전체를 후보로 확장합니다." in default.notes


def test_query_planner_defaults_country_without_context_to_target_market():
    plan = plan_contextual_query("korean fragrance")

    assert plan.entities["target_countries"] == ["KR"]
    assert plan.entities["source_countries"] == []


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


def test_advanced_score_penalizes_missing_evidence():
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
        evidence_confidence=0.0,
        market_growth_signal=0.8,
        expected_margin_rate=0.4,
    )
    assert score.total < 80
    assert score.recommendation not in {"추천", "강력 추천"}
    assert any("근거" in risk or "evidence" in risk for risk in score.risks)


def test_advanced_score_covers_low_margin_staleness_and_low_confidence():
    manufacturer = Manufacturer(id="m1", name="ABC", country="KR", categories=["beauty"], trust_level=1)
    product = Product(
        id="p1",
        manufacturer_id="m1",
        name="저마진 상품",
        category="beauty",
        keywords=[],
        suitable_channels=[],
        suitable_countries=[],
        risks=["customs_complexity", "unknown_risk"],
    )
    distributor = Distributor(id="d1", name="D", country="JP", portfolio_categories=[])
    seller = Seller(id="s1", name="S", country="JP", channels=[], categories=[])

    score = score_advanced_match(
        manufacturer,
        product,
        distributor,
        seller,
        [],
        target_country="JP",
        target_channels=[],
        evidence_confidence=0.25,
        market_growth_signal=0.0,
        expected_margin_rate=0.1,
        staleness=0.8,
    )

    assert score.economics == 2
    assert score.evidence_confidence == 2
    assert score.risk_penalty == 7
    assert score.staleness_penalty == 8
    assert score.recommendation == "비추천"
    assert "예상 실마진이 낮습니다." in score.risks
    assert "추천 근거의 신뢰도가 낮습니다." in score.risks
    assert "데이터 최신성 재검증이 필요합니다." in score.risks


def test_advanced_score_uses_product_price_margin_when_expected_margin_missing():
    manufacturer = Manufacturer(id="m1", name="ABC", country="KR", categories=["beauty"])
    product = Product(
        id="p1",
        manufacturer_id="m1",
        name="마진 상품",
        category="beauty",
        cost=500,
        suggested_price=1000,
    )
    distributor = Distributor(id="d1", name="D", country="JP")
    seller = Seller(id="s1", name="S", country="JP", channels=[])

    score = score_advanced_match(
        manufacturer,
        product,
        distributor,
        seller,
        [],
        target_country="JP",
        target_channels=[],
        evidence_confidence=1.0,
        market_growth_signal=0.0,
    )

    assert score.economics == 10


def test_advanced_score_covers_mid_margin_and_default_economics():
    manufacturer = Manufacturer(id="m1", name="ABC", country="KR", categories=["beauty"])
    product = Product(id="p1", manufacturer_id="m1", name="상품", category="beauty")
    distributor = Distributor(id="d1", name="D", country="JP")
    seller = Seller(id="s1", name="S", country="JP", channels=[])

    mid_margin = score_advanced_match(
        manufacturer,
        product,
        distributor,
        seller,
        [],
        target_country="JP",
        target_channels=[],
        evidence_confidence=1.0,
        market_growth_signal=0.0,
        expected_margin_rate=0.25,
    )
    default_margin = score_advanced_match(
        manufacturer,
        product,
        distributor,
        seller,
        [],
        target_country="JP",
        target_channels=[],
        evidence_confidence=1.0,
        market_growth_signal=0.0,
    )

    assert mid_margin.economics == 6
    assert default_margin.economics == 4


def test_advanced_score_downgrades_high_total_when_evidence_missing():
    manufacturer = Manufacturer(
        id="m1",
        name="ABC",
        country="KR",
        categories=["haircare"],
        trust_level=5,
        response_score=5,
    )
    product = Product(
        id="p1",
        manufacturer_id="m1",
        name="헤어오일",
        category="haircare",
        keywords=["hair oil", "fragrance", "damaged hair", "gift", "routine"],
        suitable_channels=["Instagram", "BASE"],
        suitable_countries=["JP"],
        moq=100,
        cost=1000,
        suggested_price=5000,
    )
    distributor = Distributor(
        id="d1",
        name="D",
        country="JP",
        warehouse_locations=["Tokyo"],
        portfolio_categories=["haircare"],
        distribution_channels=["Instagram", "BASE"],
        trade_types=["consignment"],
    )
    seller = Seller(
        id="s1",
        name="S",
        country="JP",
        channels=["Instagram", "BASE"],
        categories=["haircare"],
        trend_keywords=["hair oil", "fragrance", "damaged hair"],
        review_keywords=["gift", "routine"],
        commerce_capabilities=["content_creation", "fulfillment"],
    )
    trends = [
        Trend(
            id="t1",
            name="향 헤어",
            countries=["JP"],
            channels=["Instagram", "BASE"],
            keywords=["hair oil", "fragrance", "damaged hair", "gift", "routine"],
            related_categories=["haircare"],
            signal_strength=1.0,
        ),
        Trend(
            id="t2",
            name="선물 헤어",
            countries=["JP"],
            channels=["Instagram", "BASE"],
            keywords=["hair oil", "fragrance", "damaged hair", "gift", "routine"],
            related_categories=["haircare"],
            signal_strength=1.0,
        ),
    ]

    score = score_advanced_match(
        manufacturer,
        product,
        distributor,
        seller,
        trends,
        target_country="JP",
        target_channels=["Instagram", "BASE"],
        evidence_confidence=0.0,
        market_growth_signal=1.0,
        expected_margin_rate=0.4,
    )

    assert score.total >= 80
    assert score.recommendation == "조건부 테스트"
