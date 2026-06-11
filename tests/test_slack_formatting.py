"""Tests del formateo de resultados para Slack."""

from __future__ import annotations

from typing import Any

from blog_auditor.review.models import ReviewResult
from blog_auditor.slack.formatting import summary_blocks, summary_text


def _result(payload: dict[str, Any]) -> ReviewResult:
    return ReviewResult.model_validate(payload)


def test_summary_text_has_title_and_score(valid_review_payload: dict[str, Any]) -> None:
    text = summary_text(_result(valid_review_payload))

    assert "Toptal Pricing" in text
    assert "6.5/10" in text


def test_blocks_include_global_and_dimension_scores(valid_review_payload: dict[str, Any]) -> None:
    blocks = summary_blocks(_result(valid_review_payload))
    rendered = str(blocks)

    assert "Puntaje global: 6.5/10" in rendered
    assert "Tiene sentido: 7/10" in rendered
    assert "No genérico: 5/10" in rendered
    assert "SEO: 4/10" in rendered


def test_blocks_include_criticals_and_top_actions(valid_review_payload: dict[str, Any]) -> None:
    blocks = summary_blocks(_result(valid_review_payload))
    rendered = str(blocks)

    assert "No tiene CTA al final del artículo" in rendered
    assert "1. Agrega un CTA al final" in rendered


def test_blocks_omit_criticals_section_when_empty(valid_review_payload: dict[str, Any]) -> None:
    payload = {**valid_review_payload, "critical_issues": []}

    blocks = summary_blocks(_result(payload))

    assert "Críticos" not in str(blocks)


def test_long_sections_are_truncated(valid_review_payload: dict[str, Any]) -> None:
    payload = {**valid_review_payload, "critical_issues": ["x" * 5000]}

    blocks = summary_blocks(_result(payload))

    for block in blocks:
        text = block.get("text", {}).get("text", "")
        assert len(text) <= 3000


def test_header_title_is_truncated(valid_review_payload: dict[str, Any]) -> None:
    payload = {**valid_review_payload, "article_title": "T" * 300}

    blocks = summary_blocks(_result(payload))

    assert len(blocks[0]["text"]["text"]) <= 150
