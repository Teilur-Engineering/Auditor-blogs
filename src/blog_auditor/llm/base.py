"""Contrato que debe cumplir cualquier proveedor de LLM.

El motor de revisión depende de este protocolo, no de un proveedor concreto.
Para agregar otro proveedor (u otro modo de llamada), basta con implementar
``generate_json`` y pasarlo al ``ReviewEngine``.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Genera una respuesta JSON a partir de un prompt de sistema y uno de usuario."""

    def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        """Devuelve el JSON de la respuesta como diccionario.

        Raises:
            ProviderError: si la llamada falla o la respuesta no es JSON válido.
        """
        ...
