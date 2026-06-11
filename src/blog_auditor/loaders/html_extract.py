"""Extrae texto, jerarquía de headings y enlaces del HTML de Google Docs.

Google Docs exporta a HTML con headings reales (``<h1>``..``<h6>``) y los
hipervínculos como ``<a href>``, que el export a texto plano descarta. Se usa
``html.parser`` de la stdlib para no agregar dependencias.

Los href de Google Docs vienen envueltos en un redirect
(``https://www.google.com/url?q=URL_REAL&...``); se desenvuelven a la URL real.
"""

from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlparse

_HEADING_TAGS = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}
_BLOCK_TAGS = {"p", "li", "br", "div", "tr"}
_SKIP_TAGS = {"style", "script", "head"}


def _unwrap_google_redirect(href: str) -> str:
    """Convierte el href de redirect de Google en la URL real de destino."""
    parsed = urlparse(href)
    if parsed.netloc.endswith("google.com") and parsed.path == "/url":
        target = parse_qs(parsed.query).get("q", [])
        if target:
            return unquote(target[0])
    return href


class _GoogleDocHTMLParser(HTMLParser):
    """Acumula texto con prefijos Markdown para headings, y recolecta enlaces."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0
        self._heading_prefix: str | None = None
        self._current_href: str | None = None
        self._current_anchor: list[str] = []
        self.links: list[tuple[str, str]] = []  # (texto del ancla, url)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
            return
        if tag in _HEADING_TAGS:
            self._parts.append("\n\n" + _HEADING_TAGS[tag] + " ")
            self._heading_prefix = tag
        elif tag in _BLOCK_TAGS:
            self._parts.append("\n")
        elif tag == "a":
            href = next((value for name, value in attrs if name == "href" and value), None)
            if href:
                self._current_href = _unwrap_google_redirect(href)
                self._current_anchor = []

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if tag in _HEADING_TAGS:
            self._parts.append("\n")
            self._heading_prefix = None
        elif tag == "a" and self._current_href is not None:
            anchor = "".join(self._current_anchor).strip()
            self.links.append((anchor, self._current_href))
            self._current_href = None
            self._current_anchor = []

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        self._parts.append(data)
        if self._current_href is not None:
            self._current_anchor.append(data)

    def get_text(self) -> str:
        raw = "".join(self._parts)
        lines = [line.rstrip() for line in raw.splitlines()]
        cleaned: list[str] = []
        blank = False
        for line in lines:
            if line.strip():
                cleaned.append(line.strip())
                blank = False
            elif not blank:
                cleaned.append("")
                blank = True
        return "\n".join(cleaned).strip()


def extract_text_and_links(html: str) -> tuple[str, list[tuple[str, str]]]:
    """Devuelve (texto en markdown ligero, lista de (ancla, url))."""
    parser = _GoogleDocHTMLParser()
    parser.feed(html)
    return parser.get_text(), parser.links
