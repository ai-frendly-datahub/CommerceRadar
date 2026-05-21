from flomers_kg.advanced_scoring import AdvancedScoreBreakdown
from flomers_kg.combo_card import build_combo_card, render_combo_card_markdown
from flomers_kg.models import Distributor, Manufacturer, Product, Seller


def test_build_combo_card_includes_entities_evidence_and_breakdown():
    manufacturer = Manufacturer(id="m1", name="ABC", country="KR", categories=["haircare"])
    product = Product(id="p1", manufacturer_id="m1", name="헤어오일", category="haircare")
    distributor = Distributor(id="d1", name="Tokyo D", country="JP")
    seller = Seller(id="s1", name="Tokyo S", country="JP", channels=["BASE"])
    score = AdvancedScoreBreakdown(
        product_fit=10,
        distributor_fit=8,
        seller_fit=7,
        trend_fit=6,
        market_potential=5,
        economics=4,
        execution_feasibility=3,
        evidence_confidence=2,
        risk_penalty=1,
        staleness_penalty=0.5,
        total=43.5,
        reasons=["근거"],
        risks=["리스크"],
        recommendation="보류",
    )

    card = build_combo_card(
        manufacturer,
        product,
        distributor,
        seller,
        score,
        target_country="JP",
        target_channels=["BASE"],
        evidence_ids=["ev1"],
    )

    assert card["title"] == "ABC × Tokyo D × Tokyo S"
    assert card["entities"] == {
        "manufacturer": "ABC",
        "product": "헤어오일",
        "distributor": "Tokyo D",
        "seller": "Tokyo S",
    }
    assert card["evidence_ids"] == ["ev1"]
    assert card["breakdown"]["risk_penalty"] == 1


def test_render_combo_card_markdown_supplies_default_risk_text():
    markdown = render_combo_card_markdown(
        {
            "title": "A × B × C",
            "score": 72.0,
            "recommendation": "조건부 테스트",
            "target_country": "JP",
            "target_channels": ["Instagram", "BASE"],
            "reasons": ["제품과 채널이 맞습니다."],
            "risks": [],
            "next_actions": ["샘플 발송"],
        }
    )

    assert "# A × B × C" in markdown
    assert "- 대상 채널: Instagram, BASE" in markdown
    assert "현재 주요 리스크가 기록되지 않았습니다." in markdown
