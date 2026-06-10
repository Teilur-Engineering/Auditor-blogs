"""Esquema del resultado de una revisión.

Estos modelos son el contrato entre el LLM y la aplicación: la respuesta del
modelo se valida contra ellos antes de usarse. Si el LLM cambia o se degrada,
la validación falla de forma explícita en lugar de producir reportes rotos.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# Nombres legibles de cada dimensión, usados en el reporte.
DIMENSION_LABELS = {
    "coherence": "Tiene sentido",
    "originality": "No genérico",
    "positioning": "Posicionamiento",
    "seo": "SEO",
}


class DimensionScore(BaseModel):
    """Puntaje y hallazgos de una dimensión de revisión."""

    model_config = ConfigDict(frozen=True)

    score: int = Field(ge=0, le=10, description="Puntaje de 0 a 10")
    verdict: str = Field(min_length=1, description="Veredicto corto de una línea")
    findings: list[str] = Field(
        default_factory=list,
        description="Hallazgos concretos, citando pasajes del borrador cuando aplique",
    )


class ReviewResult(BaseModel):
    """Resultado completo de la revisión de un borrador."""

    model_config = ConfigDict(frozen=True)

    article_title: str = Field(min_length=1)
    global_score: float = Field(ge=0, le=10)
    coherence: DimensionScore
    originality: DimensionScore
    positioning: DimensionScore
    seo: DimensionScore
    search_intent: str = Field(
        min_length=1,
        description="A quién le sirve el artículo y qué busca esa persona",
    )
    strengths: list[str] = Field(default_factory=list, description="Lo que está bien")
    critical_issues: list[str] = Field(
        default_factory=list,
        description="Lo que hay que arreglar sí o sí antes de publicar",
    )
    improvements: list[str] = Field(default_factory=list, description="Mejoras sugeridas")
    actions: list[str] = Field(
        min_length=1,
        description="3-5 acciones concretas priorizadas para mejorar el artículo",
    )

    def dimensions(self) -> dict[str, DimensionScore]:
        """Dimensiones en el orden en que se muestran en el reporte."""
        return {
            "coherence": self.coherence,
            "originality": self.originality,
            "positioning": self.positioning,
            "seo": self.seo,
        }
