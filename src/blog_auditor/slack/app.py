"""Arranque del bot de Slack en Socket Mode.

Socket Mode evita exponer una URL pública: el bot abre la conexión hacia
Slack, así que puede correr en el VPS o en cualquier máquina con internet.
"""

from __future__ import annotations

import logging

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from blog_auditor.config import Settings, SlackSettings, load_settings, load_slack_settings
from blog_auditor.llm.openai_provider import OpenAIProvider
from blog_auditor.review import ReviewEngine
from blog_auditor.slack.handlers import SlackReviewer, register_handlers


def build_app(settings: Settings, slack_settings: SlackSettings) -> App:
    """Construye la app de Bolt con el motor de revisión inyectado."""
    bolt_app = App(token=slack_settings.bot_token)
    provider = OpenAIProvider(api_key=settings.openai_api_key, model=settings.model)
    reviewer = SlackReviewer(
        engine=ReviewEngine(provider),
        bot_token=slack_settings.bot_token,
        model=settings.model,
    )
    register_handlers(bolt_app, reviewer)
    return bolt_app


def run_slack_bot() -> None:
    """Valida configuración, construye la app y se conecta a Slack."""
    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    slack_settings = load_slack_settings()
    bolt_app = build_app(settings, slack_settings)
    SocketModeHandler(bolt_app, slack_settings.app_token).start()
