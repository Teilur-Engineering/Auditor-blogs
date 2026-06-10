"""Tests del renderizado del reporte Markdown."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from blog_auditor.review.models import ReviewResult
from blog_auditor.review.report import render_report


def _render(payload: dict[str, Any]) -> str:
    result = ReviewResult.model_validate(payload)
    return render_report(
        result,
        source="borrador.docx",
        model="gpt-5.4",
        reviewed_at=datetime(2026, 6, 10, 12, 0),
    )


def test_report_contains_header_and_global_score(valid_review_payload: dict[str, Any]) -> None:
    report = _render(valid_review_payload)

    assert "# Revisión de blog — Toptal Pricing" in report
    assert "PUNTAJE GLOBAL: 6.5/10" in report
    assert "borrador.docx" in report
    assert "gpt-5.4" in report
    assert "2026-06-10 12:00" in report


def test_report_contains_dimension_table(valid_review_payload: dict[str, Any]) -> None:
    report = _render(valid_review_payload)

    assert "| Tiene sentido | 7/10 |" in report
    assert "| No genérico | 5/10 |" in report
    assert "| Posicionamiento | 6/10 |" in report
    assert "| SEO | 4/10 |" in report


def test_report_contains_all_sections(valid_review_payload: dict[str, Any]) -> None:
    report = _render(valid_review_payload)

    assert "## ✅ Lo que está bien" in report
    assert "## 🔴 Problemas críticos" in report
    assert "## 🟡 Mejoras sugeridas" in report
    assert "## 📋 Acciones concretas (priorizadas)" in report
    assert "## 🔎 Search intent" in report
    assert "## Detalle por dimensión" in report


def test_actions_are_numbered(valid_review_payload: dict[str, Any]) -> None:
    report = _render(valid_review_payload)

    assert "1. Agrega un CTA al final" in report
    assert "3. Escribe una meta description" in report


def test_empty_critical_issues_show_placeholder(valid_review_payload: dict[str, Any]) -> None:
    payload = {**valid_review_payload, "critical_issues": []}

    report = _render(payload)

    assert "No se detectaron problemas críticos" in report
