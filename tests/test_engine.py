"""Tests del motor de revisión (con proveedor de LLM falso, sin llamadas reales)."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from blog_auditor.exceptions import ReviewParseError
from blog_auditor.review.engine import (
    ArticleDraft,
    ReviewEngine,
    build_system_prompt,
    build_user_prompt,
)


class FakeProvider:
    """LLMProvider de prueba que devuelve respuestas predefinidas en orden."""

    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self._responses = list(responses)
        self.calls: list[dict[str, str]] = []

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        self.calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt})
        return self._responses.pop(0)


def _draft(text: str, keyword: str | None = None) -> ArticleDraft:
    return ArticleDraft(text=text, source="borrador.md", target_keyword=keyword)


def test_review_returns_validated_result(
    valid_review_payload: dict[str, Any], sample_draft_text: str
) -> None:
    provider = FakeProvider([valid_review_payload])
    engine = ReviewEngine(provider)

    result = engine.review(_draft(sample_draft_text))

    assert result.global_score == 6.5
    assert len(provider.calls) == 1


def test_user_prompt_includes_context(
    valid_review_payload: dict[str, Any], sample_draft_text: str
) -> None:
    provider = FakeProvider([valid_review_payload])
    engine = ReviewEngine(provider)

    engine.review(_draft(sample_draft_text, keyword="toptal pricing"), today=date(2026, 6, 10))

    user_prompt = provider.calls[0]["user_prompt"]
    assert "2026-06-10" in user_prompt
    assert "toptal pricing" in user_prompt
    assert "borrador.md" in user_prompt
    assert sample_draft_text in user_prompt


def test_short_draft_is_rejected_without_calling_llm(
    valid_review_payload: dict[str, Any],
) -> None:
    provider = FakeProvider([valid_review_payload])
    engine = ReviewEngine(provider)

    with pytest.raises(ValueError, match="caracteres"):
        engine.review(_draft("Texto demasiado corto."))

    assert provider.calls == []


def test_invalid_response_triggers_one_retry(
    valid_review_payload: dict[str, Any], sample_draft_text: str
) -> None:
    provider = FakeProvider([{"basura": True}, valid_review_payload])
    engine = ReviewEngine(provider)

    result = engine.review(_draft(sample_draft_text))

    assert result.article_title.startswith("Toptal")
    assert len(provider.calls) == 2
    assert "no cumplió el esquema" in provider.calls[1]["user_prompt"]


def test_two_invalid_responses_raise_parse_error(sample_draft_text: str) -> None:
    provider = FakeProvider([{"basura": True}, {"basura": 2}])
    engine = ReviewEngine(provider)

    with pytest.raises(ReviewParseError):
        engine.review(_draft(sample_draft_text))


def test_system_prompt_includes_rubric_and_brand_context() -> None:
    system_prompt = build_system_prompt()

    assert "4 dimensiones" in system_prompt or "dimensiones" in system_prompt
    assert "TRANSPARENT PRICING" in system_prompt
    assert "Teilur" in system_prompt


def test_user_prompt_without_keyword_asks_to_infer(sample_draft_text: str) -> None:
    prompt = build_user_prompt(_draft(sample_draft_text), today=date(2026, 6, 10))

    assert "infiérela" in prompt
