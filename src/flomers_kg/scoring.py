from __future__ import annotations

from .models import Distributor, Manufacturer, MatchCandidate, Product, Seller, Trend


def overlap_score(a: list[str], b: list[str], max_score: float) -> float:
    """Return simple set-overlap score."""
    if not a or not b:
        return 0.0
    set_a = {x.lower() for x in a}
    set_b = {x.lower() for x in b}
    overlap = len(set_a & set_b)
    denominator = max(1, min(len(set_a), len(set_b)))
    return max_score * min(1.0, overlap / denominator)


def score_match(
    manufacturer: Manufacturer,
    product: Product,
    distributor: Distributor,
    seller: Seller,
    trends: list[Trend],
    target_country: str,
    target_channels: list[str],
) -> MatchCandidate:
    reasons: list[str] = []
    risks: list[str] = []

    product_fit = 0.0
    if target_country in product.suitable_countries:
        product_fit += 8
        reasons.append(f"제품이 {target_country} 적합 국가로 표시되어 있습니다.")
    product_fit += overlap_score(product.suitable_channels, target_channels, 7)
    if product.keywords:
        product_fit += min(5, len(product.keywords))
    if product.moq is not None and product.moq <= 1000:
        product_fit += 5
        reasons.append("MOQ가 낮아 소량 테스트에 유리합니다.")
    product_fit = min(product_fit, 25)

    distributor_portfolio = overlap_score([product.category], distributor.portfolio_categories, 12)
    distributor_portfolio += overlap_score(target_channels, distributor.distribution_channels, 4)
    if "consignment" in [x.lower() for x in distributor.trade_types]:
        distributor_portfolio += 4
        reasons.append("유통사가 위탁 거래를 처리할 수 있습니다.")
    distributor_portfolio = min(distributor_portfolio, 20)

    location_logistics = 0.0
    if target_country == distributor.country:
        location_logistics += 4
    if distributor.warehouse_locations:
        location_logistics += 3
    if distributor.logistics_capabilities:
        location_logistics += 3
    location_logistics = min(location_logistics, 10)

    seller_portfolio = overlap_score([product.category], seller.categories, 8)
    seller_portfolio += overlap_score(product.keywords, seller.trend_keywords + seller.review_keywords, 7)
    seller_portfolio += overlap_score(target_channels, seller.channels, 5)
    seller_portfolio = min(seller_portfolio, 20)

    trend_fit = 0.0
    for trend in trends:
        if target_country in trend.countries:
            trend_fit += overlap_score(product.keywords, trend.keywords, 5) * trend.signal_strength
            trend_fit += overlap_score([product.category], trend.related_categories, 3) * trend.signal_strength
            if any(c in trend.channels for c in target_channels):
                trend_fit += 2 * trend.signal_strength
    trend_fit = min(trend_fit, 15)
    if trend_fit >= 8:
        reasons.append("제품 키워드와 현재 트렌드 신호가 잘 연결됩니다.")

    execution = 0.0
    if manufacturer.trust_level >= 4:
        execution += 3
    if seller.commerce_capabilities:
        execution += 3
    if distributor.trade_types:
        execution += 2
    if manufacturer.response_score and manufacturer.response_score >= 4:
        execution += 2
    execution = min(execution, 10)

    risk_penalty = 0.0
    product_risks = {r.lower() for r in product.risks}
    if "certification_required" in product_risks:
        risk_penalty += 5
        risks.append("인증 확인이 필요합니다.")
    if "liquid_shipping" in product_risks:
        risk_penalty += 3
        risks.append("액체류 배송 조건을 확인해야 합니다.")
    if "ip_risk" in product_risks:
        risk_penalty += 8
        risks.append("상표권/IP 리스크 확인이 필요합니다.")
    if "high_return_risk" in product_risks:
        risk_penalty += 4
        risks.append("반품 가능성이 높습니다.")
    risk_penalty = min(risk_penalty, 20)

    total = product_fit + distributor_portfolio + location_logistics + seller_portfolio + trend_fit + execution - risk_penalty
    total = max(0.0, round(total, 1))

    if total >= 90:
        level = "강력 추천"
    elif total >= 80:
        level = "추천"
    elif total >= 70:
        level = "조건부 테스트"
    elif total >= 60:
        level = "보류"
    else:
        level = "비추천"

    next_actions = [
        "샘플 20개 발송",
        "현지어 상세페이지 1종 제작",
        "30일 소량 테스트 판매",
        "리뷰·댓글·반품 데이터를 거래 결과 테이블에 기록",
    ]

    return MatchCandidate(
        id=f"match::{manufacturer.id}::{product.id}::{distributor.id}::{seller.id}",
        manufacturer=manufacturer,
        product=product,
        distributor=distributor,
        seller=seller,
        target_country=target_country,
        target_channels=target_channels,
        score=total,
        recommendation_level=level,
        reasons=reasons,
        risks=risks,
        next_actions=next_actions,
    )
