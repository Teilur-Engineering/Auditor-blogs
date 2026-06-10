"""Loader de archivos de texto plano y Markdown."""

from __future__ import annotations

from pathlib import Path

from blog_auditor.exceptions import LoaderError


def load_text_file(path: Path) -> str:
    """Lee un archivo .txt/.md como UTF-8 (tolerando BOM de Windows)."""
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        # Archivos guardados desde Word/Notepad viejos en Windows.
        try:
            return path.read_text(encoding="cp1252")
        except UnicodeDecodeError as exc:
            raise LoaderError(
                f"No pude decodificar el archivo {path.name}. Guárdalo como UTF-8."
            ) from exc
    except OSError as exc:
        raise LoaderError(f"No pude leer el archivo {path}: {exc}") from exc
