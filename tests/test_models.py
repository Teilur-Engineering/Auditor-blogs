"""Tests del esquema de resultado de revisión."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from blog_auditor.review.models import DIMENSION_LABELS, ReviewResult


def test_valid_payload_parses(valid_review_payload: dict[str, Any]) -> None:
    result = ReviewResult.model_validate(valid_review_payload)

    assert result.article_title.startswith("Toptal Pricing")
    assert result.global_score == 6.5
    assert result.originality.score == 5


def test_score_out_of_range_fails(valid_review_payload: dict[str, Any]) -> None:
    payload = {**valid_review_payload, "global_score": 11}

    with pytest.raises(ValidationError):
        ReviewResult.model_validate(payload)


def test_dimension_score_out_of_range_fails(valid_review_payload: dict[str, Any]) -> None:
    bad_dimension = {**valid_review_payload["seo"], "score": -1}
    payload = {**valid_review_payload, "seo": bad_dimension}

    with pytest.raises(ValidationError):
        ReviewResult.model_validate(payload)


def test_empty_actions_fails(valid_review_payload: dict[str, Any]) -> None:
    payload = {**valid_review_payload, "actions": []}

    with pytest.raises(ValidationError):
        ReviewResult.model_validate(payload)


def test_result_is_immutable(valid_review_payload: dict[str, Any]) -> None:
    result = ReviewResult.model_validate(valid_review_payload)

    with pytest.raises(ValidationError):
        result.global_score = 9.0  # type: ignore[misc]


def test_dimensions_order_matches_report_labels(valid_review_payload: dict[str, Any]) -> None:
    result = ReviewResult.model_validate(valid_review_payload)

    assert list(result.dimensions().keys()) == list(DIMENSION_LABELS.keys())
