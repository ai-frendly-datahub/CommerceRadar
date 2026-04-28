# CommerceRadar

CommerceRadar is an independent workspace repository for the Flomers B2B commerce knowledge graph and matching-engine prototype. It is not a standard `radar-core` collector/report pipeline; treat it as an advanced analytics/product prototype.

## Purpose

- Model manufacturer, product, distributor, seller, trend, evidence, and transaction entities.
- Generate explainable manufacturer x product x distributor x seller combo cards.
- Connect public/operator evidence to 30-day test transactions and repeat-order learning.

## Structure

```text
CommerceRadar/
├── config/                 # ontology, source, scoring, retrieval, data-quality config
├── data/samples/           # sample JSONL entities, evidence, transactions
├── docs/                   # product, pipeline, governance, risk, and metrics docs
├── reports/                # generated/readable outputs for workspace dashboard inclusion
├── schemas/                # JSON Schema contracts for entity and output records
├── scripts/                # sample graph/search/advanced-analysis runners
├── src/flomers_kg/         # Python package
└── tests/                  # pytest coverage for graph, scoring, query planning, quality
```

## Where To Look

| Task | Location |
| --- | --- |
| Domain model | `src/flomers_kg/models.py` |
| Basic score | `src/flomers_kg/scoring.py` |
| Evidence-aware score | `src/flomers_kg/advanced_scoring.py` |
| Combo card output | `src/flomers_kg/combo_card.py` |
| Query intent/entity parsing | `src/flomers_kg/query_planner.py` |
| Data quality score | `src/flomers_kg/data_quality.py` |
| Source strategy | `docs/02_data_source_map.md`, `config/data_sources.yaml` |
| MVP product scope | `docs/18_product_requirements.md` |
| Risk and governance | `docs/08_compliance_and_governance.md`, `docs/19_risk_register.md` |

## Rules

- Keep scoring explainable. Do not replace deterministic score components with opaque model output without preserving the component breakdown.
- Every recommendation path must carry evidence IDs or an explicit placeholder for missing evidence.
- Separate manufacturer/source country from target market country in query planning and matching.
- Treat platform/social data as permissioned or policy-sensitive unless an official API or allowed public source is documented.
- Sample data is for deterministic tests only; do not treat it as production evidence.

## Commands

```bash
python3 -m pytest -q
python3 scripts/run_sample_search.py
python3 scripts/run_advanced_analysis.py
```
