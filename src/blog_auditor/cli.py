"""Interfaz de línea de comandos del Blog Auditor.

Uso típico:
    blog-auditor review borrador.docx
    blog-auditor review "https://docs.google.com/document/d/..." --keyword "toptal pricing"
"""

from __future__ import annotations

import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import typer

from blog_auditor import __version__
from blog_auditor.config import Settings, load_settings
from blog_auditor.exceptions import BlogAuditorError
from blog_auditor.llm.openai_provider import OpenAIProvider
from blog_auditor.loaders import load_draft_text
from blog_auditor.review import ArticleDraft, ReviewEngine, render_report

app = typer.Typer(
    help=f"Blog Auditor v{__version__} — revisor de calidad de borradores de blog "
    "de Teilur Talent.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def main() -> None:
    """Blog Auditor — revisor de calidad de borradores de blog de Teilur Talent."""
    # Callback vacío: fuerza el modo subcomandos (`blog-auditor review ...`)
    # y deja espacio para futuros comandos (batch de Webflow, calibración).


@app.command()
def review(
    source: str = typer.Argument(
        ...,
        help="Borrador a revisar: archivo .txt/.md/.docx o URL pública de Google Docs.",
    ),
    keyword: str | None = typer.Option(
        None,
        "--keyword",
        "-k",
        help="Keyword SEO objetivo del artículo. Si no se indica, el revisor la infiere.",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Modelo de OpenAI a usar (sobreescribe OPENAI_MODEL del .env).",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Ruta exacta donde guardar el reporte (default: carpeta reports/).",
    ),
    no_save: bool = typer.Option(
        False,
        "--no-save",
        help="Solo imprime el reporte en pantalla, sin guardar archivo.",
    ),
) -> None:
    """Revisa un borrador de blog y genera el reporte de calidad."""
    _configure_console()
    try:
        _run_review(source=source, keyword=keyword, model=model, output=output, no_save=no_save)
    except (BlogAuditorError, ValueError) as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc


def _run_review(
    *,
    source: str,
    keyword: str | None,
    model: str | None,
    output: Path | None,
    no_save: bool,
) -> None:
    settings = load_settings(model)
    text = load_draft_text(source)
    draft = ArticleDraft(text=text, source=source, target_keyword=keyword)

    typer.secho(f"Revisando '{source}' con {settings.model}...", fg=typer.colors.CYAN, err=True)
    provider = OpenAIProvider(api_key=settings.openai_api_key, model=settings.model)
    result = ReviewEngine(provider).review(draft)

    report = render_report(result, source=source, model=settings.model)
    typer.echo(report)

    if not no_save:
        report_path = output or _default_report_path(settings, result.article_title)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
        typer.secho(f"Reporte guardado en: {report_path}", fg=typer.colors.GREEN, err=True)


@app.command()
def slack() -> None:
    """Inicia el bot de Slack (Socket Mode). Requiere SLACK_BOT_TOKEN y SLACK_APP_TOKEN."""
    _configure_console()
    # Import diferido: el modo CLI no necesita slack_bolt cargado.
    from blog_auditor.slack.app import run_slack_bot

    try:
        run_slack_bot()
    except BlogAuditorError as exc:
        typer.secho(f"Error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc


def _default_report_path(settings: Settings, article_title: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return settings.reports_dir / f"{timestamp}-{_slugify(article_title)}.md"


def _slugify(value: str, max_length: int = 60) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug[:max_length] or "articulo"


def _configure_console() -> None:
    """Evita errores de encoding con emojis en consolas Windows (cp1252)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


if __name__ == "__main__":
    app()
