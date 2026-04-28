from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from flomers_kg.sample_pipeline import (
    load_distributors,
    load_manufacturers,
    load_products,
    load_sellers,
    load_trends,
)
from flomers_kg.search import contextual_match_search

DATA = ROOT / "data" / "samples"


def main() -> None:
    manufacturers = load_manufacturers(DATA / "manufacturers.jsonl")
    products = load_products(DATA / "products.jsonl")
    distributors = load_distributors(DATA / "distributors.jsonl")
    sellers = load_sellers(DATA / "sellers.jsonl")
    trends = load_trends(DATA / "trends.jsonl")

    query_keywords = ["hair oil", "fragrance", "damaged hair"]
    results = contextual_match_search(
        manufacturers=manufacturers,
        products=products,
        distributors=distributors,
        sellers=sellers,
        trends=trends,
        query_keywords=query_keywords,
        target_country="JP",
        target_channels=["Instagram", "BASE"],
        limit=3,
    )

    print("검색어: 일본에서 향·헤어 트렌드에 맞는 제조사-유통사-판매사 조합")
    print("-" * 80)
    for idx, item in enumerate(results, 1):
        print(f"추천 조합 {idx}: {item.manufacturer.name} × {item.distributor.name} × {item.seller.name}")
        print(f"제품: {item.product.name}")
        print(f"점수: {item.score} / {item.recommendation_level}")
        print("추천 근거:")
        for reason in item.reasons or ["샘플 데이터 기반 추천입니다."]:
            print(f"  - {reason}")
        print("리스크:")
        for risk in item.risks or ["중요 리스크가 샘플 데이터에 표시되지 않았습니다."]:
            print(f"  - {risk}")
        print("다음 액션:")
        for action in item.next_actions:
            print(f"  - {action}")
        print("-" * 80)


if __name__ == "__main__":
    main()
