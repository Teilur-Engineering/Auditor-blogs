"""Fixtures compartidas por la suite de tests."""

from __future__ import annotations

from typing import Any

import pytest


@pytest.fixture()
def valid_review_payload() -> dict[str, Any]:
    """Respuesta del LLM que cumple el esquema de ReviewResult."""

    def dimension(score: int) -> dict[str, Any]:
        return {
            "score": score,
            "verdict": "Veredicto corto",
            "findings": ["Hallazgo concreto"],
        }

    return {
        "article_title": "Toptal Pricing: How Much Do They Really Charge?",
        "global_score": 6.5,
        "coherence": dimension(7),
        "originality": dimension(5),
        "positioning": dimension(6),
        "seo": dimension(4),
        "search_intent": "Empresas US comparando precios de Toptal antes de contratar.",
        "strengths": ["Cita fuentes reales (Glassdoor, Reddit)"],
        "critical_issues": ["No tiene CTA al final del artículo"],
        "improvements": ["Agregar una tabla comparativa de costos"],
        "actions": [
            "Agrega un CTA al final que lleve a la página de pricing",
            "Agrega 2-3 enlaces internos a otros artículos de /insights",
            "Escribe una meta description de 150 caracteres con la keyword",
        ],
    }


@pytest.fixture()
def sample_draft_text() -> str:
    """Borrador mínimo que supera la validación de longitud del motor."""
    return (
        "# Toptal Pricing: How Much Do They Really Charge?\n\n"
        "When companies look into hiring through Toptal, the first question is "
        "always about pricing. Toptal does not publish its rates openly, which "
        "makes it hard for startups to budget. In this article we break down "
        "what is known about Toptal's real costs, based on reports from "
        "Glassdoor, Reddit and HackerNoon, and compare it with transparent "
        "alternatives for hiring senior developers in Latin America."
    )
