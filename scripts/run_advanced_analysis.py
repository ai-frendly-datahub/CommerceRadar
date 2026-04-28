from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from flomers_kg.advanced_scoring import score_advanced_match
from flomers_kg.combo_card import build_combo_card, render_combo_card_markdown
from flomers_kg.query_planner import plan_contextual_query
from flomers_kg.sample_pipeline import load_distributors, load_manufacturers, load_products, load_sellers, load_trends

SAMPLE = ROOT / "data" / "samples"

query = "일본에서 향·헤어 트렌드에 맞는 한국 제조사-유통사-판매사 조합 추천"
plan = plan_contextual_query(query)
print("검색 계획:")
print(plan)

manufacturers = load_manufacturers(SAMPLE / "manufacturers.jsonl")
products = load_products(SAMPLE / "products.jsonl")
distributors = load_distributors(SAMPLE / "distributors.jsonl")
sellers = load_sellers(SAMPLE / "sellers.jsonl")
trends = load_trends(SAMPLE / "trends.jsonl")

manufacturer = manufacturers[0]
product = products[0]
distributor = distributors[0]
seller = sellers[0]

score = score_advanced_match(
    manufacturer=manufacturer,
    product=product,
    distributor=distributor,
    seller=seller,
    trends=trends,
    target_country="JP",
    target_channels=["Instagram", "BASE"],
    evidence_confidence=0.82,
    market_growth_signal=0.78,
    expected_margin_rate=0.38,
    staleness=0.05,
)
card = build_combo_card(
    manufacturer=manufacturer,
    product=product,
    distributor=distributor,
    seller=seller,
    score=score,
    target_country="JP",
    target_channels=["Instagram", "BASE"],
    evidence_ids=["ev_product_page_001", "ev_distributor_portfolio_001", "ev_seller_reviews_001"],
)
print("\n조합 카드:\n")
print(render_combo_card_markdown(card))
