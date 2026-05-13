"""Unit tests for commerceradar.config_loader."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from commerceradar.config_loader import load_category_config


@pytest.mark.unit
def test_load_category_config_reads_yaml(tmp_path: Path) -> None:
    cat_dir = tmp_path / "categories"
    cat_dir.mkdir()
    (cat_dir / "commerce.yaml").write_text(
        yaml.safe_dump(
            {
                "category_name": "commerce",
                "display_name": "Commerce KG Radar",
                "sources": [
                    {
                        "id": "commerce_kg_trends",
                        "name": "Flomers Commerce KG Trends",
                        "type": "jsonl",
                        "url": "local://commerce/trends",
                    }
                ],
                "entities": [
                    {
                        "name": "Manufacturer",
                        "display_name": "제조사",
                        "keywords": ["manufacturer", "제조사"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    cfg = load_category_config("commerce", categories_dir=cat_dir)
    assert cfg.category_name == "commerce"
    assert cfg.display_name == "Commerce KG Radar"
    assert len(cfg.sources) == 1
    assert cfg.sources[0].id == "commerce_kg_trends"
    assert len(cfg.entities) == 1
    assert cfg.entities[0].name == "Manufacturer"
    assert "manufacturer" in cfg.entities[0].keywords


@pytest.mark.unit
def test_load_category_config_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_category_config("nonexistent", categories_dir=tmp_path)


@pytest.mark.unit
def test_load_category_config_handles_empty_lists(tmp_path: Path) -> None:
    (tmp_path / "bare.yaml").write_text(
        yaml.safe_dump({"category_name": "bare", "display_name": "Bare"}),
        encoding="utf-8",
    )
    cfg = load_category_config("bare", categories_dir=tmp_path)
    assert cfg.sources == []
    assert cfg.entities == []
