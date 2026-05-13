"""Unit tests for commerceradar.models re-exports."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from commerceradar.models import Article, CategoryConfig, EntityDefinition, Source


@pytest.mark.unit
def test_article_dataclass_fields() -> None:
    article = Article(
        title="JP fragrance hair routine",
        link="https://example.jp/trend/fragrance-hair",
        summary="fragrance, hair oil",
        published=datetime.now(UTC),
        source="sample_trend",
        category="commerce",
        matched_entities={"Country": ["JP"]},
    )
    assert article.category == "commerce"
    assert article.matched_entities["Country"] == ["JP"]


@pytest.mark.unit
def test_source_dataclass_defaults() -> None:
    source = Source(name="KG Trends", type="jsonl", url="local://commerce/trends")
    assert source.enabled is True
    assert source.trust_tier == "T3_professional"


@pytest.mark.unit
def test_entity_definition_minimal() -> None:
    entity = EntityDefinition(name="Manufacturer", display_name="제조사", keywords=["maker"])
    assert entity.name == "Manufacturer"
    assert entity.keywords == ["maker"]


@pytest.mark.unit
def test_category_config_assembled() -> None:
    cfg = CategoryConfig(
        category_name="commerce",
        display_name="Commerce",
        sources=[Source(name="KG", type="jsonl", url="local://commerce")],
        entities=[EntityDefinition(name="Channel", display_name="채널", keywords=["instagram"])],
    )
    assert cfg.category_name == "commerce"
    assert cfg.sources[0].type == "jsonl"
    assert cfg.entities[0].keywords == ["instagram"]
