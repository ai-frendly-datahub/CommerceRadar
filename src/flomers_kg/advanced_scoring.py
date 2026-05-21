from __future__ import annotations

from dataclasses import dataclass, field

from .models import Distributor, Manufacturer, Product, Seller, Trend
from .scoring import overlap_score


@dataclass
class AdvancedScoreBreakdown:
    product_fit: float = 0.0
    distributor_fit: float = 0.0
    seller_fit: float = 0.0
    trend_fit: float = 0.0
    market_potential: float = 0.0
    economics: float = 0.0
    execution_feasibility: float = 0.0
    evidence_confidence: float = 0.0
    risk_penalty: float = 0.0
    staleness_penalty: float = 0.0
    total: float = 0.0
    reasons: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    recommendation: str = ""


def _bounded(value: float, maximum: float) -> float:
    return max(0.0, min(maximum, value))


def score_advanced_match(
    manufacturer: Manufacturer,
    product: Product,
    distributor: Distributor,
    seller: Seller,
    trends: list[Trend],
    target_country: str,
    target_channels: list[str],
    evidence_confidence: float = 0.5,
    market_growth_signal: float = 0.5,
    expected_margin_rate: float | None = None,
    staleness: float = 0.0,
) -> AdvancedScoreBreakdown:
    """Evidence-aware deterministic score for early MVP ranking.

    This function keeps the model transparent. It is intentionally simple so that
    operators can challenge and tune each component before introducing ML.
    """
    reasons: list[str] = []
    risks: list[str] = []

    product_fit = 0.0
    if target_country in product.suitable_countries:
        product_fit += 5
        reasons.append(f"제품이 {target_country} 적합 국가 후보입니다.")
    product_fit += overlap_score(product.suitable_channels, target_channels, 5)
    product_fit += min(4, len(product.keywords) * 0.8)
    if product.moq is not None and product.moq <= 1000:
        product_fit += 4
        reasons.append("MOQ가 낮아 30일 소량 테스트가 가능합니다.")
    product_fit = _bounded(product_fit, 18)

    distributor_fit = overlap_score([product.category], distributor.portfolio_categories, 6)
    distributor_fit += overlap_score(target_channels, distributor.distribution_channels, 3)
    if target_country == distributor.country:
        distributor_fit += 2
    if distributor.warehouse_locations:
        distributor_fit += 2
    if "consignment" in [x.lower() for x in distributor.trade_types]:
        distributor_fit += 2
        reasons.append("유통사가 위탁 거래 조건을 처리할 수 있습니다.")
    distributor_fit = _bounded(distributor_fit, 15)

    seller_fit = overlap_score([product.category], seller.categories, 5)
    seller_fit += overlap_score(product.keywords, seller.trend_keywords + seller.review_keywords, 5)
    seller_fit += overlap_score(target_channels, seller.channels, 3)
    if "content_creation" in [x.lower() for x in seller.commerce_capabilities]:
        seller_fit += 2
        reasons.append("판매사가 콘텐츠 제작 역량을 보유합니다.")
    seller_fit = _bounded(seller_fit, 15)

    trend_fit = 0.0
    for trend in trends:
        if target_country in trend.countries:
            trend_fit += overlap_score(product.keywords, trend.keywords, 4) * trend.signal_strength
            trend_fit += overlap_score([product.category], trend.related_categories, 3) * trend.signal_strength
            trend_fit += overlap_score(target_channels, trend.channels, 2) * trend.signal_strength
    trend_fit = _bounded(trend_fit, 14)
    if trend_fit >= 7:
        reasons.append("제품 키워드와 국가/채널 트렌드가 강하게 연결됩니다.")

    market_potential = _bounded(12 * market_growth_signal, 12)
    if market_potential >= 7:
        reasons.append("시장 성장 또는 플랫폼 반응 신호가 양호합니다.")

    economics = 0.0
    if expected_margin_rate is not None:
        if expected_margin_rate >= 0.35:
            economics = 10
            reasons.append("예상 실마진이 양호합니다.")
        elif expected_margin_rate >= 0.2:
            economics = 6
        else:
            economics = 2
            risks.append("예상 실마진이 낮습니다.")
    elif product.cost and product.suggested_price:
        margin = max(0.0, (product.suggested_price - product.cost) / product.suggested_price)
        economics = _bounded(10 * margin / 0.5, 10)
    else:
        economics = 4

    execution = 0.0
    if manufacturer.trust_level >= 4:
        execution += 3
    if manufacturer.response_score and manufacturer.response_score >= 4:
        execution += 2
    if distributor.trade_types:
        execution += 1.5
    if seller.commerce_capabilities:
        execution += 1.5
    execution = _bounded(execution, 8)

    risk_map = {
        "certification_required": 6,
        "customs_complexity": 5,
        "ip_risk": 10,
        "low_margin": 7,
        "high_shipping_cost": 6,
        "liquid_shipping": 4,
        "high_return_risk": 5,
        "insufficient_evidence": 8,
    }

    evidence_score = _bounded(8 * evidence_confidence, 8)
    risk_penalty = 0.0
    if evidence_confidence <= 0:
        risk_penalty += risk_map["insufficient_evidence"]
        risks.append("추천 근거 evidence가 아직 연결되지 않았습니다.")
    elif evidence_score < 4:
        risks.append("추천 근거의 신뢰도가 낮습니다.")

    for risk in product.risks:
        penalty = risk_map.get(risk.lower(), 2)
        risk_penalty += penalty
        risks.append(f"제품 리스크 확인 필요: {risk}")
    risk_penalty = _bounded(risk_penalty, 25)

    staleness_penalty = _bounded(10 * staleness, 10)
    if staleness_penalty > 4:
        risks.append("데이터 최신성 재검증이 필요합니다.")

    total = round(
        product_fit
        + distributor_fit
        + seller_fit
        + trend_fit
        + market_potential
        + economics
        + execution
        + evidence_score
        - risk_penalty
        - staleness_penalty,
        1,
    )
    total = max(0.0, total)

    if total >= 90:
        rec = "강력 추천"
    elif total >= 80:
        rec = "추천"
    elif total >= 70:
        rec = "조건부 테스트"
    elif total >= 60:
        rec = "보류"
    else:
        rec = "비추천"
    if evidence_confidence <= 0 and rec in {"강력 추천", "추천"}:
        rec = "조건부 테스트"

    return AdvancedScoreBreakdown(
        product_fit=round(product_fit, 1),
        distributor_fit=round(distributor_fit, 1),
        seller_fit=round(seller_fit, 1),
        trend_fit=round(trend_fit, 1),
        market_potential=round(market_potential, 1),
        economics=round(economics, 1),
        execution_feasibility=round(execution, 1),
        evidence_confidence=round(evidence_score, 1),
        risk_penalty=round(risk_penalty, 1),
        staleness_penalty=round(staleness_penalty, 1),
        total=total,
        reasons=reasons,
        risks=risks,
        recommendation=rec,
    )
