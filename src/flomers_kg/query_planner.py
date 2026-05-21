from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class QueryPlan:
    intent: str
    entities: dict[str, list[str]] = field(default_factory=dict)
    retrieval_modes: list[str] = field(default_factory=list)
    expected_output: str = "combo_cards"
    notes: list[str] = field(default_factory=list)


COUNTRY_HINTS = {
    "일본": "JP",
    "JP": "JP",
    "japan": "JP",
    "japanese": "JP",
    "중국": "CN",
    "CN": "CN",
    "china": "CN",
    "chinese": "CN",
    "한국": "KR",
    "KR": "KR",
    "korea": "KR",
    "korean": "KR",
}

CHANNEL_HINTS = ["Instagram", "BASE", "Rakuten", "Xiaohongshu", "Douyin", "SmartStore", "Coupang", "Amazon"]
CATEGORY_HINTS = {
    "헤어": "haircare",
    "향": "fragrance",
    "뷰티": "beauty",
    "생활용품": "home_living",
    "수납": "storage",
    "펫": "pet",
    "굿즈": "goods",
}


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _has_source_country_context(query: str, token: str) -> bool:
    source_markers = (
        "제조사",
        "공장",
        "생산",
        "소싱",
        "브랜드",
        "manufacturer",
        "factory",
        "supplier",
        "source",
        "made in",
    )
    return any(f"{token} {marker}" in query or f"{token}{marker}" in query for marker in source_markers)


def _has_target_country_context(query: str, token: str) -> bool:
    target_markers = (
        "에서",
        "시장",
        "대상",
        "타겟",
        "판매",
        "유통",
        "수출",
        "진출",
        "market",
        "target",
        "sell",
        "export",
        "distribution",
    )
    return any(f"{token} {marker}" in query or f"{token}{marker}" in query for marker in target_markers)


def plan_contextual_query(query: str) -> QueryPlan:
    q_lower = query.lower()
    entities: dict[str, list[str]] = {
        "countries": [],
        "target_countries": [],
        "source_countries": [],
        "channels": [],
        "categories": [],
    }
    notes: list[str] = []

    for key, value in COUNTRY_HINTS.items():
        key_lower = key.lower()
        if key_lower not in q_lower:
            continue
        if _has_source_country_context(q_lower, key_lower):
            _append_unique(entities["source_countries"], value)
        if _has_target_country_context(q_lower, key_lower):
            _append_unique(entities["target_countries"], value)
        if value not in entities["source_countries"] and value not in entities["target_countries"]:
            _append_unique(entities["target_countries"], value)

    for channel in CHANNEL_HINTS:
        if channel.lower() in q_lower and channel not in entities["channels"]:
            entities["channels"].append(channel)

    for key, value in CATEGORY_HINTS.items():
        if key.lower() in q_lower and value not in entities["categories"]:
            entities["categories"].append(value)

    for value in entities["target_countries"] + entities["source_countries"]:
        _append_unique(entities["countries"], value)

    has_combo_request = "조합" in query or "추천" in query or "recommend" in q_lower
    if "왜" in query or "실패" in query:
        intent = "analyze_failure"
        output = "failure_analysis"
        modes = ["keyword", "graph", "evidence"]
    elif has_combo_request:
        intent = "recommend_combo"
        output = "combo_cards"
        modes = ["keyword", "vector", "graph", "evidence"]
    elif "찾아" in query and "조합" not in query and "추천" not in query:
        intent = "find_company"
        output = "company_list"
        modes = ["keyword", "vector", "graph"]
    elif "맞" in query or "적합" in query or "판단" in query:
        intent = "evaluate_product"
        output = "product_fit_report"
        modes = ["vector", "graph", "evidence"]
    elif "기회" in query or "틈새" in query or "트렌드" in query:
        intent = "discover_opportunity"
        output = "opportunity_report"
        modes = ["vector", "graph", "evidence"]
    else:
        intent = "recommend_combo"
        output = "combo_cards"
        modes = ["keyword", "vector", "graph", "evidence"]

    if not entities["target_countries"]:
        notes.append("대상 국가가 명확하지 않으므로 KR/JP/CN 전체를 후보로 확장합니다.")
    if entities["source_countries"] and entities["target_countries"]:
        notes.append("제조/소싱 국가와 대상 시장 국가를 분리해 검색합니다.")
    if not entities["channels"]:
        notes.append("채널이 명확하지 않으므로 카테고리별 추천 채널을 그래프에서 추론합니다.")

    return QueryPlan(intent=intent, entities=entities, retrieval_modes=modes, expected_output=output, notes=notes)
