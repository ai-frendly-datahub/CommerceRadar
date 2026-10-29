import json
from pathlib import Path

import pytest
import requests
import yaml

from commerceradar.collector import (
    _dedupe_jsonl_by_link,
    _keyword_matches_title,
    _project_root,
    collect_sources,
)
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
        """
sources:
  - id: closed
    enabled: false
    notes: 샘플이라 끔
  - id: sample_product_page
    type: sample
    url: https://example.com/abc
    enabled: true
""",
    )

    def fail_get(url: str, *, timeout: int = 20) -> _Response:
        raise AssertionError(f"disabled source must not be fetched: {url}")

    monkeypatch.setattr("commerceradar.collector._http_get", fail_get)
    articles, report = collect_sources(_config(), project_root=tmp_path, log_raw=False)

    assert articles == []
    assert report["article_count"] == 0
    assert report["source_count"] == 0
    assert report["results"][0]["status"] == "disabled"
    assert report["results"][1]["id"] == "sample_product_page"
    assert report["results"][1]["enabled"] is False
    assert "sample_product_page" not in report["sources"]
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


# Titles quoted from the 2026-10-22~28 classified sample (offtopic spec §5).
_KOSIS_NOISE_TITLES = [
    "2026년 9월 국가통계포털 퀴즈 이벤트 당첨자 발표",
    "제13회 국가승인통계 활용 디지털콘텐츠 공모전 수상작 발표",
    "2026년 9월 말 기준 KOSIS 수록자료 현행화율 공개",
    "2026년 2분기 기준 KOSIS 서비스 지연 통계 목록",
]
_CUSTOMS_NOISE_TITLES = [
    "관세청 인사(부이사관 승진)",
    "관세청, 9월의 관세인 및 3분기 핵심가치상 시상",
    "관세청 9월의 마약단속왕에 정예진 주무관 선정",
]
_CUSTOMS_USEFUL_TITLES = [
    "2026년 9월 월간 수출입 현황 [잠정치]",
    "관세청, 해외직구 전용 통관 플랫폼 정식 개통",
    "싸다고 샀다가 안전까지 위협… 두 달 새 짝퉁 28만 점 국경에서 막았다",
]


def _rss_feed(items: list[tuple[str, str]]) -> str:
    parts = [
        '<?xml version="1.0"?><rss version="2.0"><channel>',
    ]
    for title, link in items:
        parts.append(
            f"<item><title><![CDATA[{title}]]></title><link>{link}</link><description>quoted</description></item>"
        )
    parts.append("</channel></rss>")
    return "".join(parts)


def _repo_source(source_id: str) -> dict:
    payload = yaml.safe_load((_project_root() / "config" / "sources.yaml").read_text(encoding="utf-8"))
    for row in payload["sources"]:
        if row.get("id") == source_id:
            return row
    raise AssertionError(source_id)


@pytest.mark.unit
def test_sources_yaml_keeps_kosis_and_sets_notice_exclusions() -> None:
    kosis = _repo_source("kosis")
    customs = _repo_source("customs_trade_statistics")

    assert kosis["enabled"] is True
    assert kosis["config"]["exclude_title_keywords"] == [
        "이벤트",
        "당첨자",
        "공모전",
        "현행화율",
        "서비스 지연 통계",
    ]
    assert customs["config"]["exclude_title_keywords"] == ["관세청 인사", "시상", "단속왕"]


@pytest.mark.unit
def test_keyword_matches_title_uses_hangul_substring_and_ascii_word_boundary() -> None:
    event_title = _KOSIS_NOISE_TITLES[0]
    export_title = _CUSTOMS_USEFUL_TITLES[0]

    assert _keyword_matches_title("이벤트", event_title)
    assert _keyword_matches_title("당첨자", event_title)
    assert not _keyword_matches_title("이벤트", export_title)
    assert _keyword_matches_title("review", "Weekly review notes")
    assert _keyword_matches_title("review", "Weekly reviews notes")
    assert not _keyword_matches_title("review", "A reviewer note")
    assert not _keyword_matches_title("review", "preview notes")


@pytest.mark.unit
def test_collect_sources_drops_quoted_notice_titles_and_records_excluded_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    kosis = _repo_source("kosis")
    customs = _repo_source("customs_trade_statistics")
    _write_sources(
        tmp_path,
        yaml.safe_dump(
            {
                "sources": [
                    {
                        "id": "kosis",
                        "name": kosis["name"],
                        "type": "rss",
                        "url": "https://kosis.example/notice.xml",
                        "enabled": True,
                        "config": {"exclude_title_keywords": kosis["config"]["exclude_title_keywords"]},
                    },
                    {
                        "id": "customs_trade_statistics",
                        "name": customs["name"],
                        "type": "rss",
                        "url": "https://customs.example/press.xml",
                        "enabled": True,
                        "config": {"exclude_title_keywords": customs["config"]["exclude_title_keywords"]},
                    },
                    {
                        "id": "open_feed",
                        "name": "Unconfigured",
                        "type": "rss",
                        "url": "https://open.example/feed.xml",
                        "enabled": True,
                    },
                ]
            },
            allow_unicode=True,
            sort_keys=False,
        ),
    )
    feeds = {
        "https://kosis.example/notice.xml": _rss_feed(
            [(title, f"https://kosis.example/{index}") for index, title in enumerate(_KOSIS_NOISE_TITLES)]
        ),
        "https://customs.example/press.xml": _rss_feed(
            [(title, f"https://customs.example/noise-{index}") for index, title in enumerate(_CUSTOMS_NOISE_TITLES)]
            + [(title, f"https://customs.example/keep-{index}") for index, title in enumerate(_CUSTOMS_USEFUL_TITLES)]
        ),
        "https://open.example/feed.xml": _rss_feed(
            [
                (_KOSIS_NOISE_TITLES[0], "https://open.example/event"),
                (_CUSTOMS_USEFUL_TITLES[0], "https://open.example/export"),
            ]
        ),
    }

    def fake_get(url: str, *, timeout: int = 20) -> _Response:
        if url.endswith("/robots.txt"):
            return _Response(404, "missing", url=url)
        if url in feeds:
            return _Response(200, feeds[url], url=url)
        raise AssertionError(url)

    monkeypatch.setattr("commerceradar.collector._http_get", fake_get)
    articles, report = collect_sources(_config(), project_root=tmp_path, log_raw=True)

    kept = [(article.source, article.title) for article in articles]
    assert kept == [
        ("customs_trade_statistics", title) for title in _CUSTOMS_USEFUL_TITLES
    ] + [
        ("open_feed", _KOSIS_NOISE_TITLES[0]),
        ("open_feed", _CUSTOMS_USEFUL_TITLES[0]),
    ]
    assert "2026년 9월 월간 수출입 현황 [잠정치]" in [article.title for article in articles]
    by_id = {row["id"]: row for row in report["results"]}
    assert by_id["kosis"]["status"] == "ok"
    assert by_id["kosis"]["count"] == 0
    assert by_id["kosis"]["excluded_count"] == len(_KOSIS_NOISE_TITLES)
    assert by_id["customs_trade_statistics"]["count"] == len(_CUSTOMS_USEFUL_TITLES)
    assert by_id["customs_trade_statistics"]["excluded_count"] == len(_CUSTOMS_NOISE_TITLES)
    assert by_id["open_feed"]["count"] == 2
    assert by_id["open_feed"]["excluded_count"] == 0

    results_path = next((tmp_path / "data" / "raw").glob("*/source_results.json"))
    saved = json.loads(results_path.read_text(encoding="utf-8"))
    saved_by_id = {row["id"]: row for row in saved["results"]}
    assert saved_by_id["kosis"]["excluded_count"] == len(_KOSIS_NOISE_TITLES)
    assert saved_by_id["customs_trade_statistics"]["excluded_count"] == len(_CUSTOMS_NOISE_TITLES)
    assert "excluded_count" in saved_by_id["open_feed"]
    raw_path = next((tmp_path / "data" / "raw").glob("*/commerce_sources.jsonl"))
    raw_rows = [json.loads(line) for line in raw_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert [row["title"] for row in raw_rows if row["source"] == "kosis"] == []
    assert _KOSIS_NOISE_TITLES[0] in [row["title"] for row in raw_rows if row["source"] == "open_feed"]
    assert "관세청 인사(부이사관 승진)" not in [row["title"] for row in raw_rows]
    assert "2026년 9월 월간 수출입 현황 [잠정치]" in [row["title"] for row in raw_rows]
