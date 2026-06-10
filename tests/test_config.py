"""Tests de carga y validación de configuración."""

from __future__ import annotations

from pathlib import Path

import pytest

from blog_auditor.config import DEFAULT_MODEL, load_settings
from blog_auditor.exceptions import ConfigError


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("OPENAI_API_KEY", "OPENAI_MODEL", "REPORTS_DIR"):
        monkeypatch.delenv(name, raising=False)


def test_missing_api_key_raises_config_error() -> None:
    with pytest.raises(ConfigError, match="OPENAI_API_KEY"):
        load_settings(load_env_file=False)


def test_loads_key_and_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    settings = load_settings(load_env_file=False)

    assert settings.openai_api_key == "sk-test"
    assert settings.model == DEFAULT_MODEL
    assert settings.reports_dir == Path("reports")


def test_env_model_overrides_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.3")

    settings = load_settings(load_env_file=False)

    assert settings.model == "gpt-5.3"


def test_cli_override_beats_env_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.3")

    settings = load_settings("gpt-5.4-mini", load_env_file=False)

    assert settings.model == "gpt-5.4-mini"


def test_custom_reports_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("REPORTS_DIR", "salidas")

    settings = load_settings(load_env_file=False)

    assert settings.reports_dir == Path("salidas")


def test_blank_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "   ")

    with pytest.raises(ConfigError):
        load_settings(load_env_file=False)
