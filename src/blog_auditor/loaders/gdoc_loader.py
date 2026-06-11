"""Loader de Google Docs vía link público.

No requiere Google API ni OAuth: usa el endpoint de exportación, que funciona
cuando el documento está compartido como "cualquiera con el enlace puede ver".

Exporta a **HTML** (no a texto plano) para conservar dos cosas que el agente
necesita y que el texto plano pierde: la jerarquía de headings (H1/H2/H3) y los
**hipervínculos**. Los enlaces detectados se anexan al final del texto en una
sección explícita para que el revisor pueda evaluar enlaces internos de verdad,
en lugar de pedir "verificar al cargar en Webflow". Si el equipo después quiere
leer docs privados, este es el módulo a extender con la API oficial.
"""

from __future__ import annotations

import re

import httpx

from blog_auditor.exceptions import LoaderError
from blog_auditor.loaders.html_extract import extract_text_and_links

_DOC_ID_PATTERN = re.compile(r"docs\.google\.com/document/d/([a-zA-Z0-9_-]+)")
_EXPORT_URL_TEMPLATE = "https://docs.google.com/document/d/{doc_id}/export?format=html"
_REQUEST_TIMEOUT_SECONDS = 30.0


def is_google_doc_url(url: str) -> bool:
    return _DOC_ID_PATTERN.search(url) is not None


def load_google_doc(url: str) -> str:
    """Descarga un Google Doc público y devuelve su texto con los enlaces anexados."""
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

    if "accounts.google.com" in str(response.url):
        raise LoaderError(
            "Google devolvió una página de login en lugar del documento. "
            "Comparte el doc como 'Cualquier persona con el enlace puede ver' e intenta de nuevo."
        )

    text, links = extract_text_and_links(response.text)
    if not text.strip():
        raise LoaderError("El Google Doc está vacío.")

    return text + _render_links_section(links)


def _render_links_section(links: list[tuple[str, str]]) -> str:
    """Anexa los hipervínculos detectados como contexto para el revisor.

    Se hace explícito el conteo para que el agente no tenga que adivinar si el
    artículo tiene enlaces internos: los ve listados con su URL real.
    """
    real_links = [(anchor, url) for anchor, url in links if url.startswith(("http://", "https://"))]
    if not real_links:
        return (
            "\n\n=== ENLACES DETECTADOS EN EL DOCUMENTO ===\n"
            "Ninguno. El documento no contiene hipervínculos."
        )

    lines = ["\n\n=== ENLACES DETECTADOS EN EL DOCUMENTO ==="]
    for anchor, url in real_links:
        label = anchor.strip() or "(sin texto de ancla)"
        lines.append(f"- [{label}] → {url}")
    return "\n".join(lines)
