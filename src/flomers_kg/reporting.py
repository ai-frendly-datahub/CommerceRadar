from __future__ import annotations

import html
import json
from collections import Counter
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml

from .advanced_scoring import score_advanced_match
from .combo_card import build_combo_card
from .sample_pipeline import (
    load_distributors,
    load_manufacturers,
    load_products,
    load_sellers,
    load_trends,
    read_jsonl,
)


def build_report_payload(root: Path, report_date: date | None = None) -> dict[str, Any]:
    report_day = report_date or date.today()
    sample_dir = root / "data" / "samples"
    manufacturers = load_manufacturers(sample_dir / "manufacturers.jsonl")
    products = load_products(sample_dir / "products.jsonl")
    distributors = load_distributors(sample_dir / "distributors.jsonl")
    sellers = load_sellers(sample_dir / "sellers.jsonl")
    trends = load_trends(sample_dir / "trends.jsonl")
    evidence_rows = read_jsonl(sample_dir / "evidence_records.jsonl")
    transaction_rows = read_jsonl(sample_dir / "transactions.jsonl")

    manufacturer_by_id = {item.id: item for item in manufacturers}
    cards: list[dict[str, Any]] = []
    for product in products:
        manufacturer = manufacturer_by_id.get(product.manufacturer_id)
        if manufacturer is None:
            continue
        for distributor in distributors:
            if product.category not in distributor.portfolio_categories:
                continue
            for seller in sellers:
                if product.category not in seller.categories:
                    continue
                target_country = seller.country
                target_channels = _target_channels(product, distributor, seller)
                if not target_channels:
                    continue
                evidence_ids = _evidence_ids(
                    evidence_rows,
                    [manufacturer.id, product.id, distributor.id, seller.id],
                )
                evidence_status = "supported"
                if not evidence_ids:
                    evidence_ids = [
                        "evidence_pending::"
                        f"{manufacturer.id}::{product.id}::{distributor.id}::{seller.id}"
                    ]
                    evidence_status = "pending"
                evidence_confidence = _average_evidence_confidence(evidence_rows, evidence_ids)
                score = score_advanced_match(
                    manufacturer=manufacturer,
                    product=product,
                    distributor=distributor,
                    seller=seller,
                    trends=trends,
                    target_country=target_country,
                    target_channels=target_channels,
                    evidence_confidence=evidence_confidence,
                    market_growth_signal=_market_growth_signal(trends, product.category, target_country),
                    staleness=0.05,
                )
                card = build_combo_card(
                    manufacturer=manufacturer,
                    product=product,
                    distributor=distributor,
                    seller=seller,
                    score=score,
                    target_country=target_country,
                    target_channels=target_channels,
                    evidence_ids=evidence_ids,
                )
                card["id"] = (
                    f"match::{manufacturer.id}::{product.id}::{distributor.id}::{seller.id}"
                )
                card["evidence_status"] = evidence_status
                card["transaction_status"] = _transaction_status(transaction_rows, card["id"])
                cards.append(card)

    cards.sort(key=lambda item: (-float(item["score"]), str(item["title"])))
    matched_cards = [card for card in cards if float(card["score"]) >= 70.0]
    source_distribution = _sources_distribution(evidence_rows, cards)
    evidence_status_counts = Counter(str(card.get("evidence_status") or "unknown") for card in cards)

    return {
        "category": "commerce",
        "date": report_day.isoformat(),
        "generated_at": datetime.now(UTC).isoformat(),
        "article_count": len(cards),
        "matched_count": len(matched_cards),
        "source_count": _enabled_source_count(root / "config" / "sources.yaml"),
        "collected_source_count": len(source_distribution),
        "supported_evidence_count": evidence_status_counts.get("supported", 0),
        "pending_evidence_count": evidence_status_counts.get("pending", 0),
        "top_entities": _top_entities(cards),
        "sources": source_distribution,
        "distributor_distribution": _distributor_distribution(cards),
        "warnings": _report_warnings(cards),
        "cards": cards,
    }


def write_report_artifacts(
    root: Path,
    *,
    output_dir: Path | None = None,
    report_date: date | None = None,
) -> dict[str, Path]:
    reports_dir = output_dir or root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    payload = build_report_payload(root, report_date=report_date)
    token = payload["date"].replace("-", "")
    summary_path = reports_dir / f"commerce_{token}_summary.json"
    report_path = reports_dir / f"commerce_{token}.html"
    index_path = reports_dir / "index.html"

    summary_payload = {key: value for key, value in payload.items() if key != "cards"}
    summary_path.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(render_report_html(payload), encoding="utf-8")
    index_path.write_text(render_index_html(payload, report_path.name, summary_path.name), encoding="utf-8")
    return {"summary": summary_path, "report": report_path, "index": index_path}


def render_report_html(payload: dict[str, Any]) -> str:
    cards = payload["cards"]
    card_blocks = "\n".join(_render_card(card) for card in cards)
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CommerceRadar Report {html.escape(payload["date"])}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 0; background: #f5f2eb; color: #1d211c; }}
    main {{ max-width: 980px; margin: 0 auto; padding: 40px 20px; }}
    header {{ border-bottom: 3px solid #27351f; margin-bottom: 24px; }}
    h1 {{ font-size: 2rem; margin-bottom: 8px; }}
    .summary {{ display: flex; gap: 12px; flex-wrap: wrap; margin: 20px 0; }}
    .metric {{ background: #fffdf6; border: 1px solid #d4cbb8; padding: 12px 16px; border-radius: 14px; }}
    .card {{ background: #fffdf6; border: 1px solid #d4cbb8; border-radius: 18px; padding: 20px; margin: 18px 0; box-shadow: 0 10px 28px rgba(39, 53, 31, 0.08); }}
    .score {{ font-size: 1.4rem; font-weight: 700; color: #6b3d16; }}
    .chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }}
    .chip {{ background: #e7dfcf; border-radius: 999px; padding: 4px 10px; font-size: 0.9rem; }}
    li {{ margin: 4px 0; }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>CommerceRadar B2B Match Report</h1>
      <p>Generated at {html.escape(str(payload["generated_at"]))}</p>
    </header>
    <section class="summary">
      <div class="metric">Candidates: <strong>{payload["article_count"]}</strong></div>
      <div class="metric">Matched: <strong>{payload["matched_count"]}</strong></div>
      <div class="metric">Configured sources: <strong>{payload["source_count"]}</strong></div>
    </section>
    {card_blocks}
  </main>
</body>
</html>
"""


def render_index_html(payload: dict[str, Any], report_filename: str, summary_filename: str) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CommerceRadar Reports</title>
</head>
<body>
  <h1>CommerceRadar Reports</h1>
  <p>Latest report date: {html.escape(payload["date"])}</p>
  <ul>
    <li><a href="{html.escape(report_filename)}">HTML report</a></li>
    <li><a href="{html.escape(summary_filename)}">Summary JSON</a></li>
  </ul>
</body>
</html>
"""


def _render_card(card: dict[str, Any]) -> str:
    reasons = "".join(f"<li>{html.escape(str(item))}</li>" for item in card.get("reasons", []))
    risks = card.get("risks") or ["No major risk recorded."]
    risk_items = "".join(f"<li>{html.escape(str(item))}</li>" for item in risks)
    actions = "".join(f"<li>{html.escape(str(item))}</li>" for item in card.get("next_actions", []))
    channels = "".join(f'<span class="chip">{html.escape(str(item))}</span>' for item in card["target_channels"])
    evidence = "".join(f'<span class="chip">{html.escape(str(item))}</span>' for item in card.get("evidence_ids", []))
    entities = card["entities"]
    return f"""<article class="card">
  <h2>{html.escape(card["title"])}</h2>
  <p class="score">{html.escape(str(card["score"]))} / {html.escape(card["recommendation"])}</p>
  <p>{html.escape(entities["product"])} · target {html.escape(card["target_country"])}</p>
  <div class="chips">{channels}</div>
  <h3>Reasons</h3>
  <ul>{reasons}</ul>
  <h3>Risks</h3>
  <ul>{risk_items}</ul>
  <h3>Next actions</h3>
  <ul>{actions}</ul>
  <h3>Evidence</h3>
  <div class="chips">{evidence}</div>
</article>"""


def _target_channels(product: Any, distributor: Any, seller: Any) -> list[str]:
    product_channels = set(product.suitable_channels)
    distributor_channels = set(distributor.distribution_channels)
    seller_channels = set(seller.channels)
    overlap = product_channels & distributor_channels & seller_channels
    return sorted(overlap) if overlap else sorted(product_channels & seller_channels)


def _evidence_ids(rows: list[dict[str, Any]], entity_ids: list[str]) -> list[str]:
    wanted = set(entity_ids)
    ids = [
        str(row["id"])
        for row in rows
        if wanted.intersection(set(row.get("related_entities") or [])) and row.get("id")
    ]
    return sorted(set(ids))


def _average_evidence_confidence(rows: list[dict[str, Any]], evidence_ids: list[str]) -> float:
    if not evidence_ids or all(str(evidence_id).startswith("evidence_pending::") for evidence_id in evidence_ids):
        return 0.0
    wanted = set(evidence_ids)
    values = [
        float(row.get("confidence", 0.0))
        for row in rows
        if row.get("id") in wanted and isinstance(row.get("confidence"), (int, float))
    ]
    return round(sum(values) / len(values), 2) if values else 0.0


def _market_growth_signal(trends: list[Any], category: str, country: str) -> float:
    values = [
        float(trend.signal_strength)
        for trend in trends
        if country in trend.countries and category in trend.related_categories
    ]
    return round(max(values), 2) if values else 0.5


def _transaction_status(rows: list[dict[str, Any]], match_id: str) -> str | None:
    for row in rows:
        if row.get("match_id") == match_id:
            return str(row.get("status") or "")
    return None


def _enabled_source_count(path: Path) -> int:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    sources = payload.get("sources")
    if not isinstance(sources, list):
        return 0
    return sum(1 for source in sources if isinstance(source, dict) and source.get("enabled", True) is not False)


def _top_entities(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for card in cards:
        for value in card.get("entities", {}).values():
            counter[str(value)] += 1
    return [{"name": name, "count": count} for name, count in counter.most_common(5)]


def _sources_distribution(rows: list[dict[str, Any]], cards: list[dict[str, Any]]) -> dict[str, int]:
    evidence_ids = {
        evidence_id
        for card in cards
        for evidence_id in card.get("evidence_ids", [])
        if not str(evidence_id).startswith("evidence_pending::")
    }
    counter: Counter[str] = Counter()
    for row in rows:
        if row.get("id") not in evidence_ids:
            continue
        source_type = row.get("source_type")
        if source_type:
            counter[str(source_type)] += 1
    return dict(counter)


def _distributor_distribution(cards: list[dict[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for card in cards:
        entities = card.get("entities") or {}
        distributor_name = entities.get("distributor")
        if distributor_name:
            counter[str(distributor_name)] += 1
    return dict(counter)


def _report_warnings(cards: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    if not cards:
        warnings.append("no match candidates generated from sample data")
    if any(not card.get("evidence_ids") for card in cards):
        warnings.append("one or more match candidates lack evidence ids")
    return warnings
