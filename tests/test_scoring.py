from flomers_kg.models import Distributor, Manufacturer, Product, Seller, Trend
from flomers_kg.scoring import score_match
from flomers_kg.search import contextual_match_search


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
    manufacturer = Manufacturer(id="m1", name="제조사 A", country="KR", categories=["beauty"], trust_level=4)
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


def test_score_match_covers_risk_reasons_and_hold_level():
    manufacturer = Manufacturer(id="m1", name="제조사 A", country="KR", categories=["beauty"])
    product = Product(
        id="p1",
        manufacturer_id="m1",
        name="조건부 상품",
        category="beauty",
        keywords=["beauty"],
        suitable_channels=["Instagram"],
        suitable_countries=["JP"],
        risks=["liquid_shipping", "high_return_risk"],
    )
    distributor = Distributor(
        id="d1",
        name="유통사 B",
        country="JP",
        portfolio_categories=["beauty"],
        distribution_channels=["Instagram"],
        trade_types=["wholesale"],
        warehouse_locations=["Tokyo"],
        logistics_capabilities=["small_batch"],
    )
    seller = Seller(
        id="s1",
        name="판매사 C",
        country="JP",
        channels=["Instagram"],
        categories=["beauty"],
        trend_keywords=["beauty"],
        commerce_capabilities=["fulfillment"],
    )

    candidate = score_match(manufacturer, product, distributor, seller, [], "JP", ["Instagram"])

    assert 60 <= candidate.score < 70
    assert candidate.recommendation_level == "보류"
    assert "액체류 배송 조건을 확인해야 합니다." in candidate.risks
    assert "반품 가능성이 높습니다." in candidate.risks


def test_score_match_can_return_recommend_level():
    manufacturer = Manufacturer(
        id="m1",
        name="제조사 A",
        country="KR",
        categories=["haircare"],
        trust_level=4,
    )
    product = Product(
        id="p1",
        manufacturer_id="m1",
        name="헤어오일",
        category="haircare",
        keywords=["hair oil", "fragrance"],
        suitable_channels=["Instagram", "BASE"],
        suitable_countries=["JP"],
        moq=500,
        risks=[],
    )
    distributor = Distributor(
        id="d1",
        name="유통사 B",
        country="JP",
        portfolio_categories=["haircare"],
        distribution_channels=["BASE"],
        trade_types=["consignment"],
        warehouse_locations=["Tokyo"],
    )
    seller = Seller(
        id="s1",
        name="판매사 C",
        country="JP",
        channels=["Instagram", "BASE"],
        categories=["haircare"],
        trend_keywords=["hair oil"],
    )
    trend = Trend(
        id="t1",
        name="향 헤어",
        countries=["JP"],
        channels=["Instagram", "BASE"],
        keywords=["hair oil", "fragrance"],
        related_categories=["haircare"],
        signal_strength=1.0,
    )

    candidate = score_match(manufacturer, product, distributor, seller, [trend], "JP", ["Instagram", "BASE"])

    assert 80 <= candidate.score < 90
    assert candidate.recommendation_level == "추천"


def test_score_match_can_return_conditional_test_level():
    manufacturer = Manufacturer(
        id="m1",
        name="제조사 A",
        country="KR",
        categories=["haircare"],
        trust_level=4,
    )
    product = Product(
        id="p1",
        manufacturer_id="m1",
        name="헤어오일",
        category="haircare",
        keywords=["hair oil", "fragrance"],
        suitable_channels=["Instagram", "BASE"],
        suitable_countries=["JP"],
        moq=500,
        risks=[],
    )
    distributor = Distributor(
        id="d1",
        name="유통사 B",
        country="JP",
        portfolio_categories=["haircare"],
        distribution_channels=["BASE"],
        trade_types=["consignment"],
        warehouse_locations=["Tokyo"],
    )
    seller = Seller(
        id="s1",
        name="판매사 C",
        country="JP",
        channels=["Instagram", "BASE"],
        categories=["haircare"],
        trend_keywords=["hair oil"],
    )

    candidate = score_match(manufacturer, product, distributor, seller, [], "JP", ["Instagram", "BASE"])

    assert 70 <= candidate.score < 80
    assert candidate.recommendation_level == "조건부 테스트"


def test_contextual_search_filters_category_mismatches():
    manufacturer = Manufacturer(id="m1", name="제조사 A", country="KR", categories=["haircare"])
    product = Product(
        id="p1",
        manufacturer_id="m1",
        name="헤어오일",
        category="haircare",
        keywords=["hair oil", "fragrance"],
        suitable_channels=["Instagram", "BASE"],
        suitable_countries=["JP"],
    )
    good_distributor = Distributor(
        id="d1",
        name="뷰티 유통사",
        country="JP",
        portfolio_categories=["haircare"],
        distribution_channels=["BASE"],
    )
    bad_distributor = Distributor(
        id="d2",
        name="생활용품 유통사",
        country="JP",
        portfolio_categories=["home_living"],
        distribution_channels=["BASE"],
    )
    good_seller = Seller(
        id="s1",
        name="뷰티 판매사",
        country="JP",
        channels=["Instagram", "BASE"],
        categories=["haircare"],
    )
    bad_seller = Seller(
        id="s2",
        name="수납 판매사",
        country="JP",
        channels=["Instagram", "BASE"],
        categories=["storage"],
    )

    results = contextual_match_search(
        manufacturers=[manufacturer],
        products=[product],
        distributors=[good_distributor, bad_distributor],
        sellers=[good_seller, bad_seller],
        trends=[],
        query_keywords=["hair oil"],
        target_country="JP",
        target_channels=["Instagram", "BASE"],
        limit=10,
    )

    assert [result.distributor.id for result in results] == ["d1"]
    assert [result.seller.id for result in results] == ["s1"]


def test_contextual_search_filters_keyword_missing_manufacturer_country_and_channel():
    manufacturer = Manufacturer(id="m1", name="제조사 A", country="KR", categories=["haircare"])
    product = Product(
        id="p1",
        manufacturer_id="missing",
        name="헤어오일",
        category="haircare",
        keywords=["hair oil"],
        suitable_channels=["Instagram"],
    )
    good_product = Product(
        id="p2",
        manufacturer_id="m1",
        name="헤어팩",
        category="haircare",
        keywords=["hair mask"],
        suitable_channels=["Instagram"],
    )
    distributor = Distributor(
        id="d1",
        name="유통사",
        country="CN",
        portfolio_categories=["haircare"],
        distribution_channels=["Instagram"],
    )
    channel_mismatch_distributor = Distributor(
        id="d2",
        name="채널 불일치 유통사",
        country="JP",
        portfolio_categories=["haircare"],
        distribution_channels=["Rakuten"],
    )
    good_distributor = Distributor(
        id="d3",
        name="정상 유통사",
        country="JP",
        portfolio_categories=["haircare"],
        distribution_channels=["Instagram"],
    )
    seller = Seller(id="s1", name="판매사", country="JP", channels=["Instagram"], categories=["haircare"])
    wrong_country_seller = Seller(
        id="s3",
        name="타국 판매사",
        country="CN",
        channels=["Instagram"],
        categories=["haircare"],
    )
    channel_mismatch_seller = Seller(
        id="s2",
        name="채널 불일치 판매사",
        country="JP",
        channels=["Rakuten"],
        categories=["haircare"],
    )

    assert contextual_match_search(
        [manufacturer],
        [good_product],
        [distributor],
        [seller],
        [],
        query_keywords=["unmatched"],
        target_country="JP",
        target_channels=["Instagram"],
    ) == []
    assert contextual_match_search(
        [manufacturer],
        [product],
        [channel_mismatch_distributor],
        [seller],
        [],
        query_keywords=["hair oil"],
        target_country="JP",
        target_channels=["Instagram"],
    ) == []
    assert contextual_match_search(
        [manufacturer],
        [good_product],
        [channel_mismatch_distributor],
        [seller],
        [],
        query_keywords=["hair mask"],
        target_country="JP",
        target_channels=["Instagram"],
    ) == []
    assert contextual_match_search(
        [manufacturer],
        [good_product],
        [distributor],
        [seller],
        [],
        query_keywords=["hair mask"],
        target_country="JP",
        target_channels=["Instagram"],
    ) == []
    assert contextual_match_search(
        [manufacturer],
        [good_product],
        [good_distributor],
        [wrong_country_seller],
        [],
        query_keywords=["hair mask"],
        target_country="JP",
        target_channels=["Instagram"],
    ) == []
    assert contextual_match_search(
        [manufacturer],
        [good_product],
        [good_distributor],
        [channel_mismatch_seller],
        [],
        query_keywords=["hair mask"],
        target_country="JP",
        target_channels=["Instagram"],
    ) == []
