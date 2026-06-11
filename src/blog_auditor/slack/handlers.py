"""Lógica de los mensajes de Slack: de evento entrante a reporte de revisión.

Formas de pedir una revisión (por DM al bot o mencionándolo en un canal):
- Pegar el link de un Google Doc público.
- Adjuntar un archivo .docx, .pdf, .md o .txt.
- Pegar el texto del borrador directamente en el mensaje.
Opcional: indicar la keyword con ``keyword: tal cual`` en el mismo mensaje.
"""

from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from blog_auditor.exceptions import BlogAuditorError, LoaderError
from blog_auditor.loaders import load_draft_text
from blog_auditor.review import ArticleDraft, ReviewEngine, render_report
from blog_auditor.review.engine import MIN_DRAFT_LENGTH
from blog_auditor.slack.formatting import summary_blocks, summary_text

HELP_MESSAGE = (
    "👋 Soy el *Blog Auditor*. Reviso borradores de blog con el criterio de calidad "
    "de Teilur. Para pedir una revisión, envíame UNA de estas cosas:\n"
    "• El link de un Google Doc compartido como _cualquiera con el enlace puede ver_.\n"
    "• Un archivo adjunto `.docx`, `.pdf`, `.md` o `.txt`.\n"
    "• El texto del borrador pegado directo en el mensaje.\n"
    "Opcional: agrega `keyword: tu keyword objetivo` en el mismo mensaje."
)

_SUPPORTED_SUFFIXES = (".docx", ".pdf", ".md", ".markdown", ".txt")
_MENTION_PATTERN = re.compile(r"<@[A-Z0-9]+>")
_SLACK_URL_PATTERN = re.compile(r"<(https?://[^>|]+)(?:\|[^>]*)?>")
_KEYWORD_PATTERN = re.compile(r"(?:keyword|kw)\s*[:=]\s*([^\n<]+)", re.IGNORECASE)
_DOWNLOAD_TIMEOUT_SECONDS = 60.0


def extract_keyword(text: str) -> str | None:
    """Saca la keyword objetivo de un ``keyword: ...`` en el mensaje."""
    match = _KEYWORD_PATTERN.search(text)
    if match is None:
        return None
    keyword = match.group(1).strip().strip('"').strip()
    return keyword or None


def extract_url(text: str) -> str | None:
    """Saca la primera URL del mensaje (Slack las envuelve en ``<...>``)."""
    match = _SLACK_URL_PATTERN.search(text)
    return match.group(1) if match else None


def clean_pasted_text(text: str) -> str:
    """Deja solo el borrador: quita menciones, URLs y la línea de keyword."""
    without_mentions = _MENTION_PATTERN.sub("", text)
    without_urls = _SLACK_URL_PATTERN.sub("", without_mentions)
    without_keyword = _KEYWORD_PATTERN.sub("", without_urls)
    return without_keyword.strip()


def download_slack_file(file_info: dict[str, Any], bot_token: str, dest_dir: Path) -> Path:
    """Descarga un archivo adjunto de Slack usando el token del bot."""
    url = file_info.get("url_private")
    name = file_info.get("name") or "borrador"
    if not url:
        raise LoaderError("El archivo adjunto no trae URL de descarga; reintenta subirlo.")

    try:
        response = httpx.get(
            url,
            headers={"Authorization": f"Bearer {bot_token}"},
            follow_redirects=True,
            timeout=_DOWNLOAD_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError as exc:
        raise LoaderError(f"No pude descargar el archivo de Slack: {exc}") from exc

    if response.status_code != 200:
        raise LoaderError(
            f"Slack respondió {response.status_code} al descargar el archivo. "
            "Verifica que el bot esté en el canal donde se subió."
        )

    destination = dest_dir / Path(name).name
    destination.write_bytes(response.content)
    return destination


@dataclass(frozen=True)
class SlackReviewer:
    """Atiende un evento de Slack: carga el borrador, revisa y responde en hilo."""

    engine: ReviewEngine
    bot_token: str
    model: str

    def handle(self, event: dict[str, Any], say: Any, client: Any) -> None:
        thread_ts = event.get("thread_ts") or event.get("ts")
        text = event.get("text") or ""
        files = event.get("files") or []

        try:
            source_label, draft_text = self._load_draft(text, files)
        except LoaderError as exc:
            say(text=f"⚠️ {exc}", thread_ts=thread_ts)
            return

        if draft_text is None:
            say(text=HELP_MESSAGE, thread_ts=thread_ts)
            return

        say(
            text=f"🔍 Revisando *{source_label}* con `{self.model}`... esto toma 1-2 minutos.",
            thread_ts=thread_ts,
        )

        draft = ArticleDraft(
            text=draft_text, source=source_label, target_keyword=extract_keyword(text)
        )
        try:
            result = self.engine.review(draft)
        except (BlogAuditorError, ValueError) as exc:
            say(text=f"⚠️ No pude completar la revisión: {exc}", thread_ts=thread_ts)
            return

        say(blocks=summary_blocks(result), text=summary_text(result), thread_ts=thread_ts)
        report = render_report(result, source=source_label, model=self.model)
        client.files_upload_v2(
            channel=event["channel"],
            thread_ts=thread_ts,
            filename="revision-blog.md",
            title=f"Revisión: {result.article_title}"[:250],
            content=report,
        )

    def _load_draft(self, text: str, files: list[dict[str, Any]]) -> tuple[str, str | None]:
        """Resuelve la fuente del borrador en orden: adjunto → URL → texto pegado."""
        if files:
            file_info = files[0]
            name = file_info.get("name") or "borrador"
            if not name.lower().endswith(_SUPPORTED_SUFFIXES):
                raise LoaderError(
                    f"No puedo leer '{name}'. Formatos soportados: "
                    f"{', '.join(_SUPPORTED_SUFFIXES)}."
                )
            with tempfile.TemporaryDirectory() as tmp_dir:
                path = download_slack_file(file_info, self.bot_token, Path(tmp_dir))
                return name, load_draft_text(str(path))

        url = extract_url(text)
        if url:
            return url, load_draft_text(url)

        pasted = clean_pasted_text(text)
        if len(pasted) >= MIN_DRAFT_LENGTH:
            return "texto pegado en Slack", pasted

        return "", None


def register_handlers(app: Any, reviewer: SlackReviewer) -> None:
    """Conecta el reviewer a los eventos de Slack (menciones y DMs)."""

    @app.event("app_mention")
    def on_mention(event: dict[str, Any], say: Any, client: Any) -> None:
        reviewer.handle(event, say, client)

    @app.event("message")
    def on_direct_message(event: dict[str, Any], say: Any, client: Any) -> None:
        if event.get("channel_type") != "im":
            return
        if event.get("bot_id"):
            return
        if event.get("subtype") not in (None, "file_share"):
            return
        reviewer.handle(event, say, client)
