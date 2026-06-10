"""Loader de documentos Word (.docx).

Convierte los headings de Word en headings Markdown (#, ##, ...) para que el
revisor pueda evaluar la estructura H1/H2/H3 del borrador.
"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.opc.exceptions import PackageNotFoundError

from blog_auditor.exceptions import LoaderError

_MAX_HEADING_LEVEL = 6


def _heading_prefix(style_name: str) -> str | None:
    """Devuelve el prefijo Markdown si el estilo es un heading de Word."""
    if style_name == "Title":
        return "#"
    if style_name.startswith("Heading"):
        try:
            level = int(style_name.split(" ")[-1])
        except ValueError:
            level = 2
        return "#" * min(level, _MAX_HEADING_LEVEL)
    return None


def load_docx(path: Path) -> str:
    """Extrae el texto de un .docx preservando la jerarquía de headings."""
    try:
        document = Document(str(path))
    except PackageNotFoundError as exc:
        raise LoaderError(
            f"El archivo {path.name} no es un .docx válido (¿está corrupto o es .doc antiguo?)."
        ) from exc
    except OSError as exc:
        raise LoaderError(f"No pude abrir el archivo {path}: {exc}") from exc

    lines: list[str] = []
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        style_name = paragraph.style.name if paragraph.style is not None else ""
        prefix = _heading_prefix(style_name)
        lines.append(f"{prefix} {text}" if prefix else text)

    if not lines:
        raise LoaderError(f"El documento {path.name} no contiene texto.")
    return "\n\n".join(lines)
