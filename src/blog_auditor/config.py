"""Configuración de la aplicación, cargada desde variables de entorno.

La fuente de verdad es el archivo ``.env`` (ver ``.env.example``). El modelo
es configurable para poder cambiar entre modelos de OpenAI (ej. gpt-5.4 →
gpt-5.3) sin tocar el código.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from blog_auditor.exceptions import ConfigError

DEFAULT_MODEL = "gpt-5.4"
DEFAULT_REPORTS_DIR = "reports"


@dataclass(frozen=True)
class Settings:
    """Configuración inmutable validada al arranque."""

    openai_api_key: str
    model: str
    reports_dir: Path


def load_settings(
    model_override: str | None = None,
    *,
    load_env_file: bool = True,
) -> Settings:
    """Carga y valida la configuración.

    Args:
        model_override: modelo indicado por CLI; tiene prioridad sobre el .env.
        load_env_file: permite desactivar la lectura de ``.env`` en tests.

    Raises:
        ConfigError: si falta la API key de OpenAI.
    """
    if load_env_file:
        load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ConfigError(
            "Falta OPENAI_API_KEY. Copia .env.example a .env y agrega tu API key "
            "de OpenAI (https://platform.openai.com/api-keys)."
        )

    model = (model_override or "").strip() or os.getenv("OPENAI_MODEL", "").strip() or DEFAULT_MODEL
    reports_dir = Path(os.getenv("REPORTS_DIR", "").strip() or DEFAULT_REPORTS_DIR)

    return Settings(openai_api_key=api_key, model=model, reports_dir=reports_dir)
