import json
from pathlib import Path

import pytest
import requests

from commerceradar.collector import _dedupe_jsonl_by_link, _project_root, collect_sources
from commerceradar.models import CategoryConfig


def _config() -> CategoryConfig:
    return CategoryConfig(category_name="commerce", display_name="Commerce", sources=[], entities=[])


def _write_sources(root: Path, body: str) -> None:
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "sources.yaml").write_text(body, encoding="utf-8")


class _Response:
    def __init__(self, status_code: int, text: str, *, url: str = "https://example.com/item", content: bytes | None = None):
        self.status_code = status_code
        self.text = text
        self.content = text.encode("utf-8") if content is None else content
        self.url = url
        self.headers: dict[str, str] = {}


@pytest.mark.unit
def test_project_root_points_to_repository() -> None:
    assert (_project_root() / "pyproject.toml").is_file()


@pytest.mark.unit
def test_collect_sources_ignores_sample_trends(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sample_dir = tmp_path / "data" / "samples"
    sample_dir.mkdir(parents=True)
    (sample_dir / "trends.jsonl").write_text(
        '{"id":"t1","name":"가짜 샘플","source":{"source_type":"sample_trend"}}\n',
        encoding="utf-8",
    )
    _write_sources(
        tmp_path,
        "sources:\n  - id: closed\n    enabled: false\n    notes: 샘플이라 끔\n",
    )

    def fail_get(url: str, *, timeout: int = 20) -> _Response:
        raise AssertionError(f"disabled source must not be fetched: {url}")

    monkeypatch.setattr("commerceradar.collector._http_get", fail_get)
    articles, report = collect_sources(_config(), project_root=tmp_path, log_raw=False)

    assert articles == []
    assert report["article_count"] == 0
    assert report["results"][0]["status"] == "disabled"
    assert not (tmp_path / "data" / "raw").exists()


@pytest.mark.unit
def test_collect_sources_parses_rss_and_skips_robots_block(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_sources(
        tmp_path,
        """
sources:
  - id: public_rss
    name: Public
    type: rss
    url: https://news.example/feed.xml
    enabled: true
  - id: blocked_html
    name: Blocked
    type: html_meta
    url: https://blocked.example/page
    enabled: true
""",
    )
    feed = """<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <item><title>수출입 현황</title><link>https://news.example/a</link><description>9월</description></item>
      <item><title>중복</title><link>https://news.example/a</link><description>skip</description></item>
    </channel></rss>
    """

    def fake_get(url: str, *, timeout: int = 20) -> _Response:
        if url.endswith("/robots.txt"):
            if "blocked.example" in url:
                return _Response(200, "User-agent: *\nDisallow: /\n", url=url)
            return _Response(404, "missing", url=url)
        if url == "https://news.example/feed.xml":
            return _Response(200, feed, url=url)
        raise AssertionError(url)

    monkeypatch.setattr("commerceradar.collector._http_get", fake_get)
    articles, report = collect_sources(_config(), project_root=tmp_path, log_raw=False)

    assert [article.title for article in articles] == ["수출입 현황"]
    assert articles[0].source == "public_rss"
    assert articles[0].link == "https://news.example/a"
    assert report["sources"] == {"public_rss": 1, "blocked_html": 0}
    assert report["collected_source_count"] == 1
    blocked = report["results"][1]
    assert blocked["status"] == "blocked"
    assert "robots.txt" in blocked["reason"]


@pytest.mark.unit
def test_collect_sources_records_cloudflare_challenge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_sources(
        tmp_path,
        "sources:\n  - id: challenged\n    type: html_meta\n    url: https://shop.example/\n    enabled: true\n",
    )

    def fake_get(url: str, *, timeout: int = 20) -> _Response:
        if url.endswith("/robots.txt"):
            return _Response(404, "", url=url)
        response = _Response(200, "<html><title>Just a moment...</title></html>", url=url)
        response.headers["cf-mitigated"] = "challenge"
        return response

    monkeypatch.setattr("commerceradar.collector._http_get", fake_get)
    articles, report = collect_sources(_config(), project_root=tmp_path, log_raw=False)

    assert articles == []
    assert report["results"][0]["status"] == "blocked"
    assert "Cloudflare" in report["results"][0]["reason"]


@pytest.mark.unit
def test_collect_sources_parses_public_dataset_page(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_sources(
        tmp_path,
        "sources:\n  - id: factory\n    type: html_meta\n    url: https://www.data.go.kr/data/15105482/fileData.do\n    enabled: true\n",
    )
    page = """
    <html><head>
      <meta property="og:title" content="전국등록공장현황">
      <meta property="og:description" content="공장 현황 &lt;br/&gt;공개 페이지">
    </head><body>수정일 2026-09-23</body></html>
    """

    def fake_get(url: str, *, timeout: int = 20) -> _Response:
        if url.endswith("/robots.txt"):
            return _Response(200, "User-agent: Googlebot\nDisallow: /search\n", url=url)
        return _Response(200, page, url=url)

    monkeypatch.setattr("commerceradar.collector._http_get", fake_get)
    articles, report = collect_sources(_config(), project_root=tmp_path, log_raw=True)
    raw_files = list((tmp_path / "data" / "raw").glob("*/commerce_sources.jsonl"))

    assert report["sources"]["factory"] == 1
    assert articles[0].title == "전국등록공장현황"
    assert articles[0].summary.startswith("공장 현황")
    assert articles[0].published.isoformat().startswith("2026-09-23")
    assert len(raw_files) == 1
    assert "sample_trend" not in raw_files[0].read_text(encoding="utf-8")
    assert (tmp_path / "data" / "raw").joinpath(raw_files[0].parent.name, "source_results.json").is_file()


@pytest.mark.unit
def test_collect_sources_does_not_disable_tls(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []

    def fake_get(url: str, **kwargs: object) -> _Response:
        calls.append({"url": url, "kwargs": kwargs})
        if url.endswith("/robots.txt"):
            return _Response(404, "", url=url)
        return _Response(404, "missing", url=url)

    monkeypatch.setattr(requests, "get", fake_get)
    _write_sources(
        tmp_path,
        "sources:\n  - id: missing\n    type: rss\n    url: https://news.example/feed.xml\n    enabled: true\n",
    )
    articles, report = collect_sources(_config(), project_root=tmp_path, log_raw=False)

    assert articles == []
    assert report["results"][0]["status"] == "error"
    assert all("verify" not in call["kwargs"] for call in calls)


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
