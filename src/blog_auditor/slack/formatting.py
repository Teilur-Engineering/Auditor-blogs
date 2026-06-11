"""Convierte un ReviewResult en mensajes de Slack (Block Kit).

En Slack va un RESUMEN (puntajes + críticos); el reporte completo se adjunta
como archivo Markdown en el hilo, porque excede los límites de un mensaje.
"""

from __future__ import annotations

from blog_auditor.review.models import DIMENSION_LABELS, ReviewResult

_HEADER_MAX_LENGTH = 150
_SECTION_MAX_LENGTH = 2900  # límite de Block Kit es 3000; margen de seguridad


def _score_emoji(score: float) -> str:
    if score >= 8:
        return "🟢"
    if score >= 6:
        return "🟡"
    return "🔴"


def summary_text(result: ReviewResult) -> str:
    """Texto plano de respaldo (notificaciones y clientes sin Block Kit)."""
    return f"Revisión: {result.article_title} — {result.global_score:.1f}/10"


def summary_blocks(result: ReviewResult) -> list[dict]:
    """Bloques del mensaje resumen para el hilo de Slack."""
    title = result.article_title[:_HEADER_MAX_LENGTH]

    score_lines = [
        f"{_score_emoji(result.global_score)} *Puntaje global: {result.global_score:.1f}/10*",
        "",
    ]
    for key, dimension in result.dimensions().items():
        label = DIMENSION_LABELS[key]
        score_lines.append(
            f"{_score_emoji(dimension.score)} *{label}: {dimension.score}/10* — {dimension.verdict}"
        )

    blocks: list[dict] = [
        {"type": "header", "text": {"type": "plain_text", "text": title, "emoji": True}},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": _truncate("\n".join(score_lines))},
        },
    ]

    if result.critical_issues:
        criticals = "\n".join(f"• {issue}" for issue in result.critical_issues)
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": _truncate(f"*🔴 Críticos (antes de publicar):*\n{criticals}"),
                },
            }
        )

    top_actions = "\n".join(f"{i}. {action}" for i, action in enumerate(result.actions[:3], 1))
    blocks.append(
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": _truncate(f"*📋 Primeras acciones:*\n{top_actions}"),
            },
        }
    )
    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "El reporte completo con todos los hallazgos va adjunto en este hilo.",
                }
            ],
        }
    )
    return blocks


def _truncate(text: str) -> str:
    if len(text) <= _SECTION_MAX_LENGTH:
        return text
    return text[: _SECTION_MAX_LENGTH - 1] + "…"
