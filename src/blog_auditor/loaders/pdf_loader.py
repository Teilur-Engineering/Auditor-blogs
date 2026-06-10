"""Loader de documentos PDF.

La extracción de texto de un PDF pierde la jerarquía visual de headings
(H1/H2), así que para evaluar estructura es preferible .docx o Google Docs.
Se soporta porque el equipo comparte borradores exportados a PDF.
"""

from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from blog_auditor.exceptions import LoaderError


def load_pdf(path: Path) -> str:
    """Extrae el texto de un PDF, normalizando el espaciado de la extracción."""
    try:
        reader = PdfReader(str(path))
    except (PyPdfError, OSError, ValueError) as exc:
        raise LoaderError(f"No pude abrir el PDF {path.name}: {exc}") from exc

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except (PyPdfError, NotImplementedError) as exc:
            raise LoaderError(f"El PDF {path.name} está protegido con contraseña.") from exc

    pages = []
    for page in reader.pages:
        normalized = _normalize_page_text(page.extract_text() or "")
        if normalized:
            pages.append(normalized)

    if not pages:
        raise LoaderError(
            f"El PDF {path.name} no contiene texto extraíble (¿es un escaneo de imágenes?)."
        )
    return "\n\n".join(pages)


def _normalize_page_text(raw: str) -> str:
    """Compacta el texto que pypdf extrae con espacios dobles y líneas sueltas.

    Los PDF exportados de Google Docs salen con espacios duplicados entre
    palabras y palabras aisladas en líneas propias; esto los recompone en
    líneas legibles sin inventar estructura.
    """
    lines = (re.sub(r"\s+", " ", line).strip() for line in raw.splitlines())
    return "\n".join(line for line in lines if line)
