import json
from pathlib import Path

import pytest

from commerceradar.collector import _dedupe_jsonl_by_link, _project_root, collect_sources
from commerceradar.models import CategoryConfig


def _config() -> CategoryConfig:
    return CategoryConfig(category_name="commerce", display_name="Commerce", sources=[], entities=[])


@pytest.mark.unit
def test_project_root_points_to_repository() -> None:
    assert (_project_root() / "pyproject.toml").is_file()


@pytest.mark.unit
def test_collect_sources_returns_empty_list_when_trends_file_missing(tmp_path: Path) -> None:
    articles = collect_sources(_config(), project_root=tmp_path, log_raw=False)

    assert articles == []


@pytest.mark.unit
def test_collect_sources_maps_trend_fields_to_article(tmp_path: Path) -> None:
    sample_dir = tmp_path / "data" / "samples"
    sample_dir.mkdir(parents=True)
    (sample_dir / "trends.jsonl").write_text(
        (
            '{"id":"t1","name":"일본 향 헤어","countries":["JP"],"channels":["BASE"],'
            '"keywords":["hair oil","fragrance"],"related_categories":["haircare"],'
            '"source":{"source_type":"sample_trend","source_urls":["https://example.jp/trend"],'
            '"collected_at":"2026-05-01","verified_at":"2026-05-21"}}\n'
        ),
        encoding="utf-8",
    )
    article = collect_sources(_config(), project_root=tmp_path, log_raw=False)[0]

    assert article.title == "일본 향 헤어"
    assert article.link == "https://example.jp/trend"
    assert article.summary == "hair oil, fragrance"
    assert article.published.isoformat().startswith("2026-05-21")
    assert article.matched_entities == {
        "Country": ["JP"],
        "Channel": ["BASE"],
        "Category": ["haircare"],
    }
    assert article.ontology["kg_entity"] == {"type": "Trend", "id": "t1"}
    assert article.ontology["trend"]["keywords"] == ["hair oil", "fragrance"]
    assert article.ontology["extraction"]["quality_score"] == 100.0


@pytest.mark.unit
def test_collect_sources_uses_local_link_when_source_url_missing(tmp_path: Path) -> None:
    sample_dir = tmp_path / "data" / "samples"
    sample_dir.mkdir(parents=True)
    (sample_dir / "trends.jsonl").write_text(
        '{"id":"t1","name":"Untitled","countries":[],"channels":[]}\n',
        encoding="utf-8",
    )
    article = collect_sources(_config(), project_root=tmp_path, log_raw=False)[0]

    assert article.link == "local://commerce/trend/t1"
    assert article.source == "sample_trend"
    assert article.matched_entities == {}


@pytest.mark.unit
def test_collect_sources_logs_raw_articles_when_enabled(tmp_path: Path) -> None:
    sample_dir = tmp_path / "data" / "samples"
    sample_dir.mkdir(parents=True)
    (sample_dir / "trends.jsonl").write_text(
        '{"id":"t1","name":"Trend","keywords":["k"],"source":{"source_urls":["https://example.com"]}}\n',
        encoding="utf-8",
    )

    articles = collect_sources(_config(), project_root=tmp_path, log_raw=True)
    collect_sources(_config(), project_root=tmp_path, log_raw=True)
    raw_files = list((tmp_path / "data" / "raw").glob("*/commerce_kg_trends.jsonl"))

    assert len(articles) == 1
    assert len(raw_files) == 1
    raw_text = raw_files[0].read_text(encoding="utf-8")
    assert '"title": "Trend"' in raw_text
    raw_record = json.loads(raw_text)
    assert raw_record["ontology"]["kg_entity"]["id"] == "t1"
    assert len([line for line in raw_text.splitlines() if line.strip()]) == 1


@pytest.mark.unit
def test_dedupe_jsonl_by_link_keeps_latest_record(tmp_path: Path) -> None:
    path = tmp_path / "raw.jsonl"
    path.write_text(
        (
            '{"title":"old","link":"https://example.com/a"}\n'
            '{"title":"new","link":"https://example.com/a","ontology":{"kg_entity":{"id":"t1"}}}\n'
        ),
        encoding="utf-8",
    )

    duplicates = _dedupe_jsonl_by_link(path)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    assert duplicates == 1
    assert rows == [{"title": "new", "link": "https://example.com/a", "ontology": {"kg_entity": {"id": "t1"}}}]
