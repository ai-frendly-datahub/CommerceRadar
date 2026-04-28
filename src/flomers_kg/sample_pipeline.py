from __future__ import annotations

import json
from pathlib import Path
from typing import TypeVar

from .models import Distributor, Manufacturer, Product, Seller, SourceMeta, Trend

T = TypeVar("T")


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def source_from_dict(data: dict) -> SourceMeta | None:
    source = data.get("source")
    if not source:
        return None
    return SourceMeta(**source)


def load_manufacturers(path: Path) -> list[Manufacturer]:
    return [Manufacturer(source=source_from_dict(row), **{k: v for k, v in row.items() if k != "source"}) for row in read_jsonl(path)]


def load_products(path: Path) -> list[Product]:
    return [Product(source=source_from_dict(row), **{k: v for k, v in row.items() if k != "source"}) for row in read_jsonl(path)]


def load_distributors(path: Path) -> list[Distributor]:
    return [Distributor(source=source_from_dict(row), **{k: v for k, v in row.items() if k != "source"}) for row in read_jsonl(path)]


def load_sellers(path: Path) -> list[Seller]:
    return [Seller(source=source_from_dict(row), **{k: v for k, v in row.items() if k != "source"}) for row in read_jsonl(path)]


def load_trends(path: Path) -> list[Trend]:
    return [Trend(source=source_from_dict(row), **{k: v for k, v in row.items() if k != "source"}) for row in read_jsonl(path)]
