"""Collect CommerceRadar articles from configured public sources.

Sample JSONL under ``data/samples/`` is a KG seed for tests and match cards.
This collector does not turn those rows into articles.
"""

from __future__ import annotations

import html
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib import robotparser

import feedparser
import requests
import yaml

from .models import Article, CategoryConfig


USER_AGENT = "CommerceRadar/1.0 (+https://github.com/ai-frendly-datahub/CommerceRadar)"
_HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml, text/html, */*"}
_MAX_ITEMS = 30
_TIMEOUT_SECONDS = 20


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _dedupe_jsonl_by_link(path: Path) -> int:
    """Rewrite a raw article JSONL file with one latest record per link."""
    if not path.exists():
        return 0
    records: list[dict[str, Any]] = []
    index_by_link: dict[str, int] = {}
    duplicates = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            link = str(record.get("link") or "")
            if link and link in index_by_link:
                duplicates += 1
                records[index_by_link[link]] = record
                continue
            if link:
                index_by_link[link] = len(records)
            records.append(record)
    if duplicates:
        with path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return duplicates


def _http_get(url: str, *, timeout: int = _TIMEOUT_SECONDS) -> requests.Response:
    """GET with TLS verification left at the requests default (on)."""
    return requests.get(url, headers=_HEADERS, timeout=timeout)


def _load_sources(root: Path) -> list[dict[str, Any]]:
    path = root / "config" / "sources.yaml"
    if not path.exists():
        return []
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    sources = payload.get("sources")
    if not isinstance(sources, list):
        return []
    return [row for row in sources if isinstance(row, dict)]


def _robots_allows(url: str) -> tuple[bool, str]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False, "수집 URL이 없음"
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = _http_get(robots_url)
    except requests.RequestException as exc:
        return False, f"robots.txt 확인 실패: {exc}"
    if response.status_code == 404:
        return True, ""
    if response.status_code >= 400:
        return False, f"robots.txt HTTP {response.status_code}"
    parser = robotparser.RobotFileParser()
    parser.parse(response.text.splitlines())
    if parser.can_fetch(USER_AGENT, url):
        return True, ""
    return False, "robots.txt가 이 경로를 차단"


def _challenge_reason(response: requests.Response) -> str | None:
    if response.status_code in {401, 403}:
        return f"HTTP {response.status_code} 인증 또는 접근 거부"
    mitigated = (response.headers.get("cf-mitigated") or "").lower()
    if mitigated:
        return "Cloudflare 챌린지"
    head = response.text[:2500].lower()
    if "just a moment" in head or "cf-challenge" in head or "attention required" in head:
        return "Cloudflare 챌린지"
    return None


def _strip_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _entry_published(entry: Any) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if isinstance(parsed, time.struct_time):
        return datetime(*parsed[:6], tzinfo=UTC)
    return None


def _parse_rss(content: bytes, *, source_id: str, category: str) -> list[Article]:
    feed = feedparser.parse(content)
    articles: list[Article] = []
    seen: set[str] = set()
    for entry in feed.entries[:_MAX_ITEMS]:
        link = str(entry.get("link") or "").strip()
        if not link or link in seen:
            continue
        seen.add(link)
        title = _strip_text(str(entry.get("title") or "")) or "(no title)"
        summary = _strip_text(str(entry.get("summary") or entry.get("description") or ""))
        articles.append(
            Article(
                title=title,
                link=link,
                summary=summary[:500],
                published=_entry_published(entry),
                source=source_id,
                category=category,
                collected_at=datetime.now(UTC),
            )
        )
    return articles


def _meta_content(page: str, prop: str) -> str:
    pattern = rf'<meta[^>]+(?:property|name)=["\']{re.escape(prop)}["\'][^>]+content=["\']([^"\']*)["\']'
    match = re.search(pattern, page, flags=re.I)
    if match:
        return html.unescape(match.group(1)).strip()
    pattern = rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:property|name)=["\']{re.escape(prop)}["\']'
    match = re.search(pattern, page, flags=re.I)
    if match:
        return html.unescape(match.group(1)).strip()
    return ""


def _parse_html_meta(page: str, *, url: str, source_id: str, category: str) -> list[Article]:
    title = _meta_content(page, "og:title")
    if not title:
        match = re.search(r"<title>(.*?)</title>", page, flags=re.I | re.S)
        title = _strip_text(match.group(1)) if match else ""
    if not title:
        return []
    summary = _strip_text(_meta_content(page, "og:description") or _meta_content(page, "description"))
    published = None
    dated = re.search(r"(?:수정일|등록일)[^0-9]{0,40}(20\d{2}-\d{2}-\d{2})", page)
    if dated:
        published = datetime.fromisoformat(dated.group(1)).replace(tzinfo=UTC)
    return [
        Article(
            title=title,
            link=url,
            summary=summary[:500],
            published=published,
            source=source_id,
            category=category,
            collected_at=datetime.now(UTC),
        )
    ]


def _result(
    source: dict[str, Any],
    *,
    status: str,
    count: int = 0,
    reason: str = "",
) -> dict[str, Any]:
    return {
        "id": str(source.get("id") or source.get("name") or "unknown"),
        "name": str(source.get("name") or source.get("id") or ""),
        "enabled": source.get("enabled", True) is not False,
        "url": str(source.get("url") or ""),
        "status": status,
        "count": count,
        "reason": reason or str(source.get("notes") or ""),
    }


def _collect_one(source: dict[str, Any], *, category: str) -> tuple[list[Article], dict[str, Any]]:
    source_id = str(source.get("id") or source.get("name") or "unknown")
    if source_id.startswith("sample_") or str(source.get("type") or "").startswith("sample"):
        skipped = _result(
            source,
            status="disabled",
            reason="샘플 출처는 정기 수집에서 제외",
        )
        skipped["enabled"] = False
        return [], skipped
    if source.get("enabled", True) is False:
        return [], _result(source, status="disabled")
    url = str(source.get("url") or "").strip()
    if not url:
        return [], _result(source, status="error", reason="수집 URL이 없음")
    allowed, robots_reason = _robots_allows(url)
    if not allowed:
        return [], _result(source, status="blocked", reason=robots_reason)
    try:
        response = _http_get(url)
    except requests.RequestException as exc:
        return [], _result(source, status="error", reason=f"요청 실패: {exc}")
    challenge = _challenge_reason(response)
    if challenge:
        return [], _result(source, status="blocked", reason=challenge)
    if response.status_code == 404:
        return [], _result(source, status="error", reason="HTTP 404")
    if response.status_code >= 400:
        return [], _result(source, status="error", reason=f"HTTP {response.status_code}")
    source_type = str(source.get("type") or "").lower()
    try:
        if source_type == "rss":
            articles = _parse_rss(response.content, source_id=source_id, category=category)
        elif source_type in {"html_meta", "html"}:
            articles = _parse_html_meta(response.text, url=str(response.url), source_id=source_id, category=category)
        else:
            return [], _result(source, status="error", reason=f"지원하지 않는 수집 타입: {source.get('type')}")
    except Exception as exc:
        return [], _result(source, status="error", reason=f"파싱 오류: {exc}")
    if not articles:
        return [], _result(source, status="error", reason="파싱 결과가 비어 있음")
    return articles, _result(source, status="ok", count=len(articles), reason="")


def _collection_report(results: list[dict[str, Any]], articles: list[Article]) -> dict[str, Any]:
    enabled = [row for row in results if row.get("enabled")]
    counts: dict[str, int] = {}
    for row in enabled:
        counts[str(row["id"])] = int(row.get("count") or 0)
    return {
        "article_count": len(articles),
        "source_count": len(enabled),
        "collected_source_count": sum(1 for count in counts.values() if count > 0),
        "sources": counts,
        "results": results,
    }


def collect_sources(
    config: CategoryConfig,
    *,
    project_root: Path | None = None,
    log_raw: bool = True,
) -> tuple[list[Article], dict[str, Any]]:
    """Fetch enabled sources in ``config/sources.yaml``.

    Sample trend rows are ignored. TLS verification is not disabled.
    robots.txt disallow, HTTP 401/403, and Cloudflare challenges are recorded
    and skipped.
    """
    root = project_root if project_root is not None else _project_root()
    articles: list[Article] = []
    results: list[dict[str, Any]] = []
    for source in _load_sources(root):
        source_articles, result = _collect_one(source, category=config.category_name)
        articles.extend(source_articles)
        results.append(result)

    report = _collection_report(results, articles)
    if log_raw:
        raw_dir = root / "data" / "raw" / datetime.now(UTC).date().isoformat()
        raw_dir.mkdir(parents=True, exist_ok=True)
        (raw_dir / "source_results.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if articles:
            from radar_core.raw_logger import RawLogger

            output_path = RawLogger(root / "data" / "raw").log(articles, source_name="commerce_sources")
            _dedupe_jsonl_by_link(output_path)
    return articles, report
