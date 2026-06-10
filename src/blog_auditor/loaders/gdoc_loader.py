"""Loader de Google Docs vía link público.

No requiere Google API ni OAuth: usa el endpoint de exportación a texto plano,
que funciona cuando el documento está compartido como "cualquiera con el
enlace puede ver". Si el equipo después quiere leer docs privados, este es el
módulo a extender con la API oficial de Google Docs.
"""

from __future__ import annotations

import re

import httpx

from blog_auditor.exceptions import LoaderError

_DOC_ID_PATTERN = re.compile(r"docs\.google\.com/document/d/([a-zA-Z0-9_-]+)")
_EXPORT_URL_TEMPLATE = "https://docs.google.com/document/d/{doc_id}/export?format=txt"
_REQUEST_TIMEOUT_SECONDS = 30.0


def is_google_doc_url(url: str) -> bool:
    return _DOC_ID_PATTERN.search(url) is not None


def load_google_doc(url: str) -> str:
    """Descarga el contenido de un Google Doc compartido por enlace."""
    match = _DOC_ID_PATTERN.search(url)
    if match is None:
        raise LoaderError(
            "La URL no parece un Google Doc (esperaba docs.google.com/document/d/...)."
        )

    export_url = _EXPORT_URL_TEMPLATE.format(doc_id=match.group(1))
    try:
        response = httpx.get(export_url, follow_redirects=True, timeout=_REQUEST_TIMEOUT_SECONDS)
    except httpx.HTTPError as exc:
        raise LoaderError(f"No pude conectarme a Google Docs: {exc}") from exc

    if response.status_code != 200:
        raise LoaderError(
            f"Google Docs respondió {response.status_code}. Verifica que el documento "
            "esté compartido como 'Cualquier persona con el enlace puede ver'."
        )

    text = response.text
    if "<html" in text[:500].lower():
        raise LoaderError(
            "Google devolvió una página de login en lugar del documento. "
            "Comparte el doc como 'Cualquier persona con el enlace puede ver' e intenta de nuevo."
        )

    if not text.strip():
        raise LoaderError("El Google Doc está vacío.")
    return text
