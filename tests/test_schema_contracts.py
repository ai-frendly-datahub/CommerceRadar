import json
from pathlib import Path

from jsonschema import Draft202012Validator

from flomers_kg.reporting import build_report_payload


ROOT = Path(__file__).resolve().parents[1]


def _jsonl_rows(path: Path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            yield json.loads(line)


def test_sample_jsonl_records_match_schemas():
    schema_pairs = {
        "manufacturers.jsonl": "manufacturer.schema.json",
        "products.jsonl": "product.schema.json",
        "distributors.jsonl": "distributor.schema.json",
        "sellers.jsonl": "seller.schema.json",
        "trends.jsonl": "trend.schema.json",
        "evidence_records.jsonl": "evidence.schema.json",
        "transactions.jsonl": "transaction_result.schema.json",
    }

    for data_name, schema_name in schema_pairs.items():
        schema = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema)
        for row in _jsonl_rows(ROOT / "data" / "samples" / data_name):
            validator.validate(row)


def test_generated_combo_cards_match_schema():
    schema = json.loads((ROOT / "schemas" / "combo_card.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    payload = build_report_payload(ROOT)

    assert payload["cards"]
    for card in payload["cards"]:
        validator.validate(card)
