from __future__ import annotations

from .advanced_scoring import AdvancedScoreBreakdown
from .models import Distributor, Manufacturer, Product, Seller


def build_combo_card(
    manufacturer: Manufacturer,
    product: Product,
    distributor: Distributor,
    seller: Seller,
    score: AdvancedScoreBreakdown,
    target_country: str,
    target_channels: list[str],
    evidence_ids: list[str] | None = None,
) -> dict:
    return {
        "title": f"{manufacturer.name} × {distributor.name} × {seller.name}",
        "score": score.total,
        "recommendation": score.recommendation,
        "entities": {
            "manufacturer": manufacturer.name,
            "product": product.name,
            "distributor": distributor.name,
            "seller": seller.name,
        },
        "target_country": target_country,
        "target_channels": target_channels,
        "reasons": score.reasons,
        "risks": score.risks,
        "next_actions": [
            "샘플 20개 발송",
            "현지어 상세페이지 1종 제작",
            "KOC 또는 판매사 30일 테스트 진행",
            "주문·댓글·반품·실마진 데이터를 거래 결과로 기록",
        ],
        "evidence_ids": evidence_ids or [],
        "breakdown": {
            "product_fit": score.product_fit,
            "distributor_fit": score.distributor_fit,
            "seller_fit": score.seller_fit,
            "trend_fit": score.trend_fit,
            "market_potential": score.market_potential,
            "economics": score.economics,
            "execution_feasibility": score.execution_feasibility,
            "evidence_confidence": score.evidence_confidence,
            "risk_penalty": score.risk_penalty,
            "staleness_penalty": score.staleness_penalty,
        },
    }


def render_combo_card_markdown(card: dict) -> str:
    lines = [
        f"# {card['title']}",
        "",
        f"- 점수: {card['score']}",
        f"- 추천: {card['recommendation']}",
        f"- 대상 국가: {card['target_country']}",
        f"- 대상 채널: {', '.join(card['target_channels'])}",
        "",
        "## 추천 근거",
    ]
    lines += [f"- {reason}" for reason in card.get("reasons", [])]
    lines += ["", "## 리스크"]
    risks = card.get("risks", []) or ["현재 주요 리스크가 기록되지 않았습니다."]
    lines += [f"- {risk}" for risk in risks]
    lines += ["", "## 다음 액션"]
    lines += [f"- {action}" for action in card.get("next_actions", [])]
    return "\n".join(lines)
