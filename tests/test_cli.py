"""Tests de la CLI (con proveedor falso, sin llamadas reales a OpenAI)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from blog_auditor import cli
from blog_auditor.config import Settings

runner = CliRunner()


@pytest.fixture()
def fake_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    valid_review_payload: dict[str, Any],
) -> Path:
    """Settings y proveedor falsos para ejercitar la CLI de punta a punta."""
    settings = Settings(
        openai_api_key="sk-test",
        model="gpt-5.4",
        reports_dir=tmp_path / "reports",
    )
    monkeypatch.setattr(cli, "load_settings", lambda model_override=None: settings)

    class FakeOpenAIProvider:
        def __init__(self, api_key: str, model: str) -> None:
            self.model = model

        def generate_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
            return valid_review_payload

    monkeypatch.setattr(cli, "OpenAIProvider", FakeOpenAIProvider)
    return tmp_path


def _write_draft(directory: Path, sample_draft_text: str) -> Path:
    draft = directory / "borrador.md"
    draft.write_text(sample_draft_text, encoding="utf-8")
    return draft


def test_review_prints_report(fake_environment: Path, sample_draft_text: str) -> None:
    draft = _write_draft(fake_environment, sample_draft_text)

    result = runner.invoke(cli.app, ["review", str(draft), "--no-save"])

    assert result.exit_code == 0
    assert "PUNTAJE GLOBAL: 6.5/10" in result.output


def test_review_saves_report_to_reports_dir(fake_environment: Path, sample_draft_text: str) -> None:
    draft = _write_draft(fake_environment, sample_draft_text)

    result = runner.invoke(cli.app, ["review", str(draft)])

    assert result.exit_code == 0
    saved = list((fake_environment / "reports").glob("*.md"))
    assert len(saved) == 1
    assert "toptal-pricing" in saved[0].name


def test_review_saves_to_explicit_output(fake_environment: Path, sample_draft_text: str) -> None:
    draft = _write_draft(fake_environment, sample_draft_text)
    output = fake_environment / "salida" / "reporte.md"

    result = runner.invoke(cli.app, ["review", str(draft), "--output", str(output)])

    assert result.exit_code == 0
    assert output.exists()
    assert "PUNTAJE GLOBAL" in output.read_text(encoding="utf-8")


def test_missing_file_exits_with_error(fake_environment: Path) -> None:
    result = runner.invoke(cli.app, ["review", str(fake_environment / "no-existe.md")])

    assert result.exit_code == 1
    assert "Error" in result.output


def test_slugify_handles_accents_and_symbols() -> None:
    slug = cli._slugify("¿Cuánto cobra Toptal? — Análisis 2026")

    assert slug == "cuanto-cobra-toptal-analisis-2026"
    assert cli._slugify("***") == "articulo"
