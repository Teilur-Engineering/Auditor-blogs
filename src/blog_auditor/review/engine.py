"""Motor de revisión: orquesta prompts, llamada al LLM y validación.

El motor no sabe nada de CLI ni de OpenAI en concreto: recibe un
``LLMProvider`` y devuelve un ``ReviewResult`` validado. Esto permite
reutilizarlo desde Slack, una web o un barrido batch de Webflow sin cambios.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from importlib import resources

from pydantic import ValidationError

from blog_auditor.exceptions import ReviewParseError
from blog_auditor.llm.base import LLMProvider
from blog_auditor.review.models import ReviewResult

# Un borrador más corto que esto no es un artículo: evita gastar tokens en
# revisar textos vacíos o pegados a medias.
MIN_DRAFT_LENGTH = 300

_PROMPTS_PACKAGE = "blog_auditor.prompts"


@dataclass(frozen=True)
class ArticleDraft:
    """Borrador de artículo a revisar."""

    text: str
    source: str
    target_keyword: str | None = None


def load_prompt(filename: str) -> str:
    """Lee un prompt empaquetado con la librería."""
    return resources.files(_PROMPTS_PACKAGE).joinpath(filename).read_text(encoding="utf-8")


def build_system_prompt() -> str:
    """Prompt de sistema = rúbrica de revisión + contexto de marca de Teilur."""
    rubric = load_prompt("system_prompt.md")
    brand = load_prompt("brand_context.md")
    return f"{rubric}\n\n{brand}"


def build_user_prompt(draft: ArticleDraft, today: date) -> str:
    keyword = draft.target_keyword or "No especificada — infiérela del contenido del borrador."
    return (
        f"Fecha actual: {today.isoformat()}\n"
        f"Keyword objetivo: {keyword}\n"
        f"Fuente del borrador: {draft.source}\n\n"
        "=== BORRADOR A REVISAR ===\n"
        f"{draft.text}\n"
        "=== FIN DEL BORRADOR ==="
    )


class ReviewEngine:
    """Ejecuta una revisión completa de un borrador."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def review(self, draft: ArticleDraft, today: date | None = None) -> ReviewResult:
        """Revisa un borrador y devuelve el resultado validado.

        Si la primera respuesta del LLM no cumple el esquema, reintenta una
        vez informándole el error de validación.

        Raises:
            ValueError: si el borrador está vacío o es demasiado corto.
            ProviderError: si la llamada al LLM falla.
            ReviewParseError: si el LLM no produce un resultado válido tras el reintento.
        """
        text = draft.text.strip()
        if len(text) < MIN_DRAFT_LENGTH:
            raise ValueError(
                f"El borrador tiene {len(text)} caracteres; se necesitan al menos "
                f"{MIN_DRAFT_LENGTH}. ¿Se cargó el documento correcto?"
            )

        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(draft, today or date.today())

        raw = self._provider.generate_json(system_prompt=system_prompt, user_prompt=user_prompt)
        try:
            return ReviewResult.model_validate(raw)
        except ValidationError as first_error:
            retry_prompt = (
                f"{user_prompt}\n\n"
                "Tu respuesta anterior no cumplió el esquema JSON requerido. "
                f"Errores de validación:\n{first_error}\n"
                "Responde de nuevo cumpliendo EXACTAMENTE el esquema, "
                "sin texto fuera del JSON."
            )
            raw_retry = self._provider.generate_json(
                system_prompt=system_prompt, user_prompt=retry_prompt
            )
            try:
                return ReviewResult.model_validate(raw_retry)
            except ValidationError as second_error:
                raw_excerpt = json.dumps(raw_retry, ensure_ascii=False)[:2000]
                raise ReviewParseError(
                    "El LLM no produjo una revisión válida tras dos intentos. "
                    f"Último error de validación:\n{second_error}\n"
                    f"Última respuesta recibida:\n{raw_excerpt}"
                ) from second_error
