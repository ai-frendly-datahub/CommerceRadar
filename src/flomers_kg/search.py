from __future__ import annotations

from .models import Distributor, Manufacturer, Product, Seller, Trend
from .scoring import score_match


def _overlaps(a: list[str], b: list[str]) -> bool:
    return bool({item.lower() for item in a} & {item.lower() for item in b})


def contextual_match_search(
    manufacturers: list[Manufacturer],
    products: list[Product],
    distributors: list[Distributor],
    sellers: list[Seller],
    trends: list[Trend],
    query_keywords: list[str],
    target_country: str,
    target_channels: list[str],
    limit: int = 5,
):
    """Naive contextual search prototype.

    This MVP uses keyword overlap and deterministic scoring. Later versions should
    add vector search, graph traversal, source citation, and LLM-based reasoning.
    """
    keyword_set = {k.lower() for k in query_keywords}
    products_by_manufacturer = {p.manufacturer_id: [] for p in products}
    for product in products:
        products_by_manufacturer.setdefault(product.manufacturer_id, []).append(product)

    manufacturer_by_id = {m.id: m for m in manufacturers}
    candidates = []

    for product in products:
        product_terms = {product.category.lower(), *[k.lower() for k in product.keywords], product.name.lower()}
        if keyword_set and not (keyword_set & product_terms):
            continue
        manufacturer = manufacturer_by_id.get(product.manufacturer_id)
        if not manufacturer:
            continue
        for distributor in distributors:
            if distributor.country != target_country:
                continue
            if product.category not in distributor.portfolio_categories:
                continue
            if (
                target_channels
                and distributor.distribution_channels
                and not _overlaps(target_channels, distributor.distribution_channels)
            ):
                continue
            for seller in sellers:
                if seller.country != target_country:
                    continue
                if product.category not in seller.categories:
                    continue
                if (
                    target_channels
                    and seller.channels
                    and not _overlaps(target_channels, seller.channels)
                ):
                    continue
                candidate = score_match(
                    manufacturer=manufacturer,
                    product=product,
                    distributor=distributor,
                    seller=seller,
                    trends=trends,
                    target_country=target_country,
                    target_channels=target_channels,
                )
                candidates.append(candidate)

    candidates.sort(key=lambda c: c.score, reverse=True)
    return candidates[:limit]
