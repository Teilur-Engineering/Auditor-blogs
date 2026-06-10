"""Renderiza el resultado de una revisión como reporte Markdown.

El formato replica el acordado en la propuesta (docs/PROPUESTA-AGENTE-CALIDAD-BLOGS.md,
sección 5): veredicto rápido para la manager + lista accionable para la redactora.
"""

from __future__ import annotations

from datetime import datetime

from blog_auditor.review.models import DIMENSION_LABELS, ReviewResult


def _bullet_section(title: str, items: list[str], empty_note: str) -> str:
    lines = [f"## {title}", ""]
    if items:
        lines.extend(f"- {item}" for item in items)
    else:
        lines.append(f"_{empty_note}_")
    lines.append("")
    return "\n".join(lines)


def _numbered_section(title: str, items: list[str]) -> str:
    lines = [f"## {title}", ""]
    lines.extend(f"{index}. {item}" for index, item in enumerate(items, start=1))
    lines.append("")
    return "\n".join(lines)


def render_report(
    result: ReviewResult,
    *,
    source: str,
    model: str,
    reviewed_at: datetime | None = None,
) -> str:
    """Genera el reporte completo en Markdown."""
    timestamp = (reviewed_at or datetime.now()).strftime("%Y-%m-%d %H:%M")

    header = [
        f"# Revisión de blog — {result.article_title}",
        "",
        f"- **Fuente:** {source}",
        f"- **Fecha de revisión:** {timestamp}",
        f"- **Modelo:** {model}",
        "",
        f"## PUNTAJE GLOBAL: {result.global_score:.1f}/10",
        "",
        "| Dimensión | Puntaje | Veredicto |",
        "|---|---|---|",
    ]
    for key, dimension in result.dimensions().items():
        label = DIMENSION_LABELS[key]
        header.append(f"| {label} | {dimension.score}/10 | {dimension.verdict} |")
    header.append("")

    sections = [
        "\n".join(header),
        _bullet_section("✅ Lo que está bien", result.strengths, "Sin puntos destacables."),
        _bullet_section(
            "🔴 Problemas críticos (arreglar antes de publicar)",
            result.critical_issues,
            "No se detectaron problemas críticos.",
        ),
        _bullet_section("🟡 Mejoras sugeridas", result.improvements, "Sin mejoras sugeridas."),
        _numbered_section("📋 Acciones concretas (priorizadas)", result.actions),
        f"## 🔎 Search intent\n\n{result.search_intent}\n",
        _render_findings(result),
    ]
    return "\n".join(sections).rstrip() + "\n"


def _render_findings(result: ReviewResult) -> str:
    lines = ["## Detalle por dimensión", ""]
    for key, dimension in result.dimensions().items():
        label = DIMENSION_LABELS[key]
        lines.append(f"### {label} — {dimension.score}/10")
        lines.append("")
        if dimension.findings:
            lines.extend(f"- {finding}" for finding in dimension.findings)
        else:
            lines.append("_Sin hallazgos adicionales._")
        lines.append("")
    return "\n".join(lines)
