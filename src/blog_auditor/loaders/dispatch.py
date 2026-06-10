"""Decide qué loader usar según la fuente indicada por el usuario.

Fuentes soportadas:
- Archivo local ``.txt`` / ``.md`` / ``.markdown``
- Archivo local ``.docx`` (Word / exportado de Google Docs)
- URL de Google Docs compartida como "cualquiera con el enlace"
"""

from __future__ import annotations

from pathlib import Path

from blog_auditor.exceptions import LoaderError
from blog_auditor.loaders.docx_loader import load_docx
from blog_auditor.loaders.gdoc_loader import is_google_doc_url, load_google_doc
from blog_auditor.loaders.text_loader import load_text_file

_TEXT_SUFFIXES = {".txt", ".md", ".markdown"}


def load_draft_text(source: str) -> str:
    """Carga el texto del borrador desde la fuente indicada.

    Args:
        source: ruta a un archivo local o URL de Google Docs.

    Raises:
        LoaderError: si la fuente no existe o no está soportada.
    """
    source = source.strip()
    if not source:
        raise LoaderError("La fuente del borrador está vacía.")

    if source.startswith(("http://", "https://")):
        if is_google_doc_url(source):
            return load_google_doc(source)
        raise LoaderError(
            "Solo se soportan URLs de Google Docs (docs.google.com/document/...). "
            "Este agente revisa BORRADORES, no páginas publicadas; si el artículo "
            "ya está publicado, copia el texto a un archivo local."
        )

    path = Path(source)
    if not path.exists():
        raise LoaderError(f"No existe el archivo: {path}")
    if not path.is_file():
        raise LoaderError(f"La ruta no es un archivo: {path}")

    suffix = path.suffix.lower()
    if suffix in _TEXT_SUFFIXES:
        return load_text_file(path)
    if suffix == ".docx":
        return load_docx(path)

    raise LoaderError(
        f"Formato no soportado: '{suffix or '(sin extensión)'}'. "
        "Formatos válidos: .txt, .md, .docx o URL de Google Docs."
    )
