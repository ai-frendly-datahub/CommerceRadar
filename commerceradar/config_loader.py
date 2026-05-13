"""Load CommerceRadar category configuration."""

from __future__ import annotations

from pathlib import Path

import yaml

from .models import CategoryConfig, EntityDefinition, Source


_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_category_config(
    category_name: str,
    *,
    categories_dir: Path | None = None,
) -> CategoryConfig:
    base = categories_dir if categories_dir is not None else _PROJECT_ROOT / "config" / "categories"
    config_file = Path(base) / f"{category_name}.yaml"
    if not config_file.exists():
        raise FileNotFoundError(f"Category config not found: {config_file}")

    payload = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
    sources = [Source(**row) for row in payload.get("sources", []) or []]
    entities = [
        EntityDefinition(
            name=row["name"],
            keywords=list(row.get("keywords") or []),
            display_name=row.get("display_name") or row["name"],
        )
        for row in payload.get("entities", []) or []
    ]
    return CategoryConfig(
        category_name=payload.get("category_name", category_name),
        display_name=payload.get("display_name", category_name),
        sources=sources,
        entities=entities,
    )
