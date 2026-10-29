import json
from pathlib import Path

import pytest

from commerceradar.quality_report import build_quality_report
from commerceradar.sample_filter import is_sample_row, split_sample_rows, tag_sample_rows

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.unit
def test_is_sample_row_detects_tag_source_and_source_meta() -> None:
    assert is_sample_row({"is_sample": True})
    assert is_sample_row({"source": "sample_trend"})
    assert is_sample_row({"ontology": {"source_meta": {"source_type": "sample_trend"}}})
    assert not is_sample_row({"source": "kosis", "link": "https://kosis.kr/x"})
    assert not is_sample_row({})


@pytest.mark.unit
def test_split_and_tag_do_not_mutate_inputs() -> None:
    rows = [{"source": "sample_trend", "link": "a"}, {"source": "kosis", "link": "b"}]
    real, samples = split_sample_rows(rows)
    assert [r["link"] for r in real] == ["b"]
    assert [r["link"] for r in samples] == ["a"]
    tagged = tag_sample_rows(samples, reason="demo")
    assert tagged[0]["is_sample"] is True and tagged[0]["sample_reason"] == "demo"
    assert "is_sample" not in rows[0]


@pytest.mark.unit
def test_quality_report_excludes_sample_rows_from_real_raw_metrics(tmp_path: Path) -> None:
    raw_dir = tmp_path / "data" / "raw" / "2026-10-19"
    raw_dir.mkdir(parents=True)
    rows = [
        {"link": "https://example.jp/trend/a", "source": "sample_trend"},
        {"link": "https://example.jp/trend/a", "source": "sample_trend"},
        {"link": "https://kosis.kr/n/1", "source": "kosis", "is_sample": False},
    ]
    (raw_dir / "commerce_kg_trends.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
    )

    checks = build_quality_report(tmp_path)["data_quality_checks"]

    assert checks["raw_trend_rows"] == 1
    assert checks["raw_trend_sample_rows_excluded"] == 2
    assert checks["raw_trend_duplicate_link_count"] == 0


@pytest.mark.unit
def test_repository_sample_manifest_matches_seed_and_tagged_copy() -> None:
    manifest = json.loads((ROOT / "data/samples/SAMPLE_MANIFEST.json").read_text(encoding="utf-8"))
    seed = [
        json.loads(line)
        for line in (ROOT / manifest["seed_file"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    tagged = [
        json.loads(line)
        for line in (ROOT / manifest["tagged_copy"]).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    ids = {item["id"] for item in manifest["items"]}

    assert len(manifest["items"]) == 2
    assert ids == {row["id"] for row in seed}
    assert ids == {row["ontology"]["kg_entity"]["id"] for row in tagged}
    assert all(row["is_sample"] is True and is_sample_row(row) for row in tagged)
    assert {item["link"] for item in manifest["items"]} == {row["link"] for row in tagged}
