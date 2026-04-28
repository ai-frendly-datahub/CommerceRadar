from flomers_kg.models import Distributor, Manufacturer, Product, Seller, Trend
from flomers_kg.scoring import score_match


def test_score_match_returns_candidate():
    manufacturer = Manufacturer(
        id="m1",
        name="제조사 A",
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
        keywords=["hair oil", "fragrance", "gift"],
        suitable_channels=["Instagram", "BASE"],
        suitable_countries=["JP"],
        risks=[],
        moq=500,
    )
    distributor = Distributor(
        id="d1",
        name="유통사 B",
        country="JP",
        portfolio_categories=["haircare"],
        distribution_channels=["BASE"],
        trade_types=["consignment"],
        warehouse_locations=["Tokyo"],
        logistics_capabilities=["small_batch"],
    )
    seller = Seller(
        id="s1",
        name="판매사 C",
        country="JP",
        channels=["Instagram", "BASE"],
        categories=["haircare"],
        trend_keywords=["hair oil", "fragrance"],
        review_keywords=["gift"],
        commerce_capabilities=["content_creation"],
    )
    trend = Trend(
        id="t1",
        name="향 헤어 트렌드",
        countries=["JP"],
        channels=["Instagram", "BASE"],
        keywords=["hair oil", "fragrance"],
        related_categories=["haircare"],
        signal_strength=1.0,
    )

    candidate = score_match(manufacturer, product, distributor, seller, [trend], "JP", ["Instagram", "BASE"])
    assert candidate.score > 70
    assert candidate.recommendation_level in {"조건부 테스트", "추천", "강력 추천"}
    assert candidate.next_actions


def test_score_match_penalizes_risk():
    manufacturer = Manufacturer(id="m1", name="제조사 A", country="KR", categories=["beauty"])
    product = Product(
        id="p1",
        manufacturer_id="m1",
        name="위험 상품",
        category="beauty",
        keywords=["beauty"],
        suitable_channels=["Instagram"],
        suitable_countries=["JP"],
        risks=["ip_risk", "certification_required"],
    )
    distributor = Distributor(id="d1", name="유통사 B", country="JP", portfolio_categories=["beauty"])
    seller = Seller(id="s1", name="판매사 C", country="JP", channels=["Instagram"], categories=["beauty"])
    candidate = score_match(manufacturer, product, distributor, seller, [], "JP", ["Instagram"])
    assert candidate.score < 70
    assert candidate.risks
