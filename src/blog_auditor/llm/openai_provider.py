"""Proveedor de LLM basado en la API de OpenAI.

Usa ``response_format={"type": "json_object"}`` en lugar de structured outputs
estrictos para mantener compatibilidad entre modelos (gpt-5.4, gpt-5.3, etc.);
la validación fuerte del esquema la hace el motor con Pydantic.
"""

from __future__ import annotations

import json
from typing import Any

from openai import OpenAI, OpenAIError

from blog_auditor.exceptions import ProviderError

DEFAULT_TIMEOUT_SECONDS = 180.0


class OpenAIProvider:
    """Implementación de ``LLMProvider`` sobre la API de chat de OpenAI."""

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._client = OpenAI(api_key=api_key, timeout=timeout)
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
        except OpenAIError as exc:
            raise ProviderError(
                f"Error llamando a OpenAI con el modelo '{self._model}': {exc}"
            ) from exc

        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise ProviderError("OpenAI devolvió una respuesta vacía.")

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ProviderError("OpenAI no devolvió un JSON válido.") from exc

        if not isinstance(payload, dict):
            raise ProviderError("OpenAI devolvió JSON pero no es un objeto.")
        return payload
