from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from flomers_kg.graph import KnowledgeGraph
from flomers_kg.sample_pipeline import load_distributors, load_manufacturers, load_products, load_sellers, load_trends

DATA = ROOT / "data" / "samples"


def main() -> None:
    graph = KnowledgeGraph()
    manufacturers = load_manufacturers(DATA / "manufacturers.jsonl")
    products = load_products(DATA / "products.jsonl")
    distributors = load_distributors(DATA / "distributors.jsonl")
    sellers = load_sellers(DATA / "sellers.jsonl")
    trends = load_trends(DATA / "trends.jsonl")

    for manufacturer in manufacturers:
        graph.add_node(manufacturer.id, "Manufacturer", name=manufacturer.name, categories=manufacturer.categories)
    for product in products:
        graph.add_node(product.id, "Product", name=product.name, category=product.category, keywords=product.keywords)
        graph.add_edge(product.manufacturer_id, "PRODUCES", product.id)
    for distributor in distributors:
        graph.add_node(distributor.id, "Distributor", name=distributor.name, country=distributor.country, categories=distributor.portfolio_categories)
    for seller in sellers:
        graph.add_node(seller.id, "Seller", name=seller.name, country=seller.country, categories=seller.categories)
    for trend in trends:
        graph.add_node(trend.id, "Trend", name=trend.name, keywords=trend.keywords)
        for product in products:
            if set(product.keywords) & set(trend.keywords):
                graph.add_edge(product.id, "MATCHES_TREND", trend.id)

    print(f"노드 수: {len(graph.nodes)}")
    print(f"엣지 수: {len(graph.edges)}")
    print("헤어오일 인접 노드:", graph.neighbors("p_perfume_hair_oil"))


if __name__ == "__main__":
    main()
