"""Helpers that keep sample (demo) rows out of real collection metrics.

CommerceRadar's KG seed trends (``data/samples/trends.jsonl``) were once
republished into ``data/raw/<date>/commerce_kg_trends.jsonl``. Those rows are
not collected public data: they use ``source=sample_trend`` and example.jp URLs,
and their ``published`` date is a fixed past date (2026-05-21).

Nothing is deleted. Rows stay where they are; this module only lets callers
recognise them (``is_sample``) so they can be left out of real metrics.
"""

from __future__ import annotations

from typing import Any

SAMPLE_PREFIX = "sample"


def _starts_with_sample(value: object) -> bool:
    return isinstance(value, str) and value.strip().lower().startswith(SAMPLE_PREFIX)


def is_sample_row(row: dict[str, Any]) -> bool:
    """Return True when ``row`` is a sample/demo row rather than collected data."""
    if row.get("is_sample") is True:
        return True
    if _starts_with_sample(row.get("source")):
        return True
    ontology = row.get("ontology")
    if isinstance(ontology, dict):
        if ontology.get("is_sample") is True:
            return True
        source_meta = ontology.get("source_meta")
        if isinstance(source_meta, dict) and _starts_with_sample(source_meta.get("source_type")):
            return True
    return False


def split_sample_rows(
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split rows into ``(real_rows, sample_rows)`` without mutating them."""
    real: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    for row in rows:
        (samples if is_sample_row(row) else real).append(row)
    return real, samples


def tag_sample_rows(rows: list[dict[str, Any]], *, reason: str) -> list[dict[str, Any]]:
    """Return copies of ``rows`` with ``is_sample`` and ``sample_reason`` set."""
    return [{**row, "is_sample": True, "sample_reason": reason} for row in rows]
