from datetime import date
from pathlib import Path

from flomers_kg.reporting import (
    _enabled_source_count,
    _report_warnings,
    _sources_distribution,
    build_report_payload,
    render_report_html,
)


SAMPLE_FILES = [
    "manufacturers.jsonl",
    "products.jsonl",
    "distributors.jsonl",
    "sellers.jsonl",
    "trends.jsonl",
    "evidence_records.jsonl",
    "transactions.jsonl",
]


def _empty_project_root(tmp_path: Path) -> Path:
    sample_dir = tmp_path / "data" / "samples"
    sample_dir.mkdir(parents=True)
    for name in SAMPLE_FILES:
        (sample_dir / name).write_text("", encoding="utf-8")
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "sources.yaml").write_text(
        "sources:\n  - id: sample\n    enabled: true\n", encoding="utf-8"
    )
    return tmp_path


def test_build_report_payload_warns_when_no_candidates(tmp_path: Path):
    root = _empty_project_root(tmp_path)

    payload = build_report_payload(root, report_date=date(2026, 5, 21))

    assert payload["article_count"] == 0
    assert payload["matched_count"] == 0
    assert payload["source_count"] == 1
    assert payload["collected_source_count"] == 0
    assert payload["warnings"] == ["no match candidates generated from sample data"]


def test_build_report_payload_skips_missing_manufacturer_and_empty_channels(tmp_path: Path):
    root = _empty_project_root(tmp_path)
    sample_dir = root / "data" / "samples"
    (sample_dir / "manufacturers.jsonl").write_text(
        '{"id":"m1","name":"M","country":"KR","categories":["haircare"]}\n',
        encoding="utf-8",
    )
    (sample_dir / "products.jsonl").write_text(
        (
            '{"id":"p_missing","manufacturer_id":"missing","name":"P","category":"haircare"}\n'
            '{"id":"p_no_channel","manufacturer_id":"m1","name":"P2","category":"haircare",'
            '"suitable_channels":["BASE"]}\n'
        ),
        encoding="utf-8",
    )
    (sample_dir / "distributors.jsonl").write_text(
        '{"id":"d1","name":"D","country":"JP","portfolio_categories":["haircare"],"distribution_channels":["Rakuten"]}\n',
        encoding="utf-8",
    )
    (sample_dir / "sellers.jsonl").write_text(
        '{"id":"s1","name":"S","country":"JP","channels":["Instagram"],"categories":["haircare"]}\n',
        encoding="utf-8",
    )

    payload = build_report_payload(root)

    assert payload["cards"] == []
    assert payload["warnings"] == ["no match candidates generated from sample data"]


def test_enabled_source_count_handles_non_list_sources(tmp_path: Path):
    path = tmp_path / "sources.yaml"
    path.write_text("sources:\n  enabled: true\n", encoding="utf-8")

    assert _enabled_source_count(path) == 0


def test_source_distribution_skips_unreferenced_evidence():
    rows = [
        {"id": "ev1", "source_type": "sample"},
        {"id": "ev2", "source_type": "unused"},
        {"id": "ev3"},
    ]
    cards = [
        {"evidence_ids": ["ev1", "ev3", "evidence_pending::x"]},
    ]

    assert _sources_distribution(rows, cards) == {"sample": 1}


def test_report_warnings_flags_cards_without_evidence_ids():
    warnings = _report_warnings([{"evidence_ids": []}])

    assert warnings == ["one or more match candidates lack evidence ids"]


def test_render_report_html_escapes_card_content():
    html = render_report_html(
        {
            "date": "2026-05-21",
            "generated_at": "<generated>",
            "article_count": 1,
            "matched_count": 1,
            "source_count": 1,
            "cards": [
                {
                    "title": "<Match>",
                    "score": 70,
                    "recommendation": "조건부 테스트",
                    "entities": {"product": "<Product>"},
                    "target_country": "JP",
                    "target_channels": ["BASE<script>"],
                    "reasons": ["<reason>"],
                    "risks": ["<risk>"],
                    "next_actions": ["<action>"],
                    "evidence_ids": ["<ev>"],
                }
            ],
        }
    )

    assert "<Match>" not in html
    assert "&lt;Match&gt;" in html
    assert "&lt;reason&gt;" in html
    assert "&lt;ev&gt;" in html
