"""Tests de la lógica de mensajes de Slack (sin conexión real a Slack ni OpenAI)."""

from __future__ import annotations

from typing import Any

import pytest

from blog_auditor.review.models import ReviewResult
from blog_auditor.slack import handlers
from blog_auditor.slack.handlers import (
    HELP_MESSAGE,
    SlackReviewer,
    clean_pasted_text,
    extract_keyword,
    extract_url,
)

# ── Parsing de mensajes ─────────────────────────────────────────


def test_extract_keyword_variants() -> None:
    assert extract_keyword("keyword: toptal pricing") == "toptal pricing"
    assert extract_keyword("revisa esto kw= devops hiring") == "devops hiring"
    assert extract_keyword('KEYWORD: "upwork fees"') == "upwork fees"
    assert extract_keyword("sin keyword aquí") is None


def test_extract_url_unwraps_slack_format() -> None:
    text = "revisa <https://docs.google.com/document/d/abc/edit|este doc> porfa"

    assert extract_url(text) == "https://docs.google.com/document/d/abc/edit"
    assert extract_url("sin enlaces") is None


def test_clean_pasted_text_removes_noise() -> None:
    text = "<@U12345> keyword: toptal\nEste es el borrador real. <https://x.com|link>"

    assert clean_pasted_text(text) == "Este es el borrador real."


# ── SlackReviewer ───────────────────────────────────────────────


class FakeEngine:
    def __init__(self, result: ReviewResult) -> None:
        self._result = result
        self.drafts: list[Any] = []

    def review(self, draft: Any) -> ReviewResult:
        self.drafts.append(draft)
        return self._result


class FakeSay:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


class FakeClient:
    def __init__(self) -> None:
        self.uploads: list[dict[str, Any]] = []

    def files_upload_v2(self, **kwargs: Any) -> None:
        self.uploads.append(kwargs)


@pytest.fixture()
def reviewer_env(valid_review_payload: dict[str, Any]) -> dict[str, Any]:
    result = ReviewResult.model_validate(valid_review_payload)
    engine = FakeEngine(result)
    reviewer = SlackReviewer(engine=engine, bot_token="xoxb-test", model="gpt-5.4")  # type: ignore[arg-type]
    return {"reviewer": reviewer, "engine": engine, "say": FakeSay(), "client": FakeClient()}


def _event(text: str = "", files: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {"text": text, "files": files or [], "ts": "111.222", "channel": "C123"}


def test_empty_message_gets_help(reviewer_env: dict[str, Any]) -> None:
    reviewer_env["reviewer"].handle(
        _event("<@U999> hola"), reviewer_env["say"], reviewer_env["client"]
    )

    assert reviewer_env["say"].calls[0]["text"] == HELP_MESSAGE
    assert reviewer_env["engine"].drafts == []


def test_pasted_text_is_reviewed(reviewer_env: dict[str, Any], sample_draft_text: str) -> None:
    reviewer_env["reviewer"].handle(
        _event(f"keyword: toptal pricing\n{sample_draft_text}"),
        reviewer_env["say"],
        reviewer_env["client"],
    )

    draft = reviewer_env["engine"].drafts[0]
    assert draft.source == "texto pegado en Slack"
    assert draft.target_keyword == "toptal pricing"
    # Mensajes: "revisando" + resumen con bloques
    assert "Revisando" in reviewer_env["say"].calls[0]["text"]
    assert "blocks" in reviewer_env["say"].calls[1]
    # Reporte completo adjunto en el hilo
    upload = reviewer_env["client"].uploads[0]
    assert upload["channel"] == "C123"
    assert "PUNTAJE GLOBAL" in upload["content"]


def test_gdoc_url_is_loaded_and_reviewed(
    reviewer_env: dict[str, Any], sample_draft_text: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    url = "https://docs.google.com/document/d/abc/edit"
    monkeypatch.setattr(handlers, "load_draft_text", lambda source: sample_draft_text)

    reviewer_env["reviewer"].handle(
        _event(f"revisa <{url}>"), reviewer_env["say"], reviewer_env["client"]
    )

    assert reviewer_env["engine"].drafts[0].source == url


def test_attached_file_is_downloaded_and_reviewed(
    reviewer_env: dict[str, Any], sample_draft_text: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeResponse:
        status_code = 200
        content = sample_draft_text.encode("utf-8")

    captured: dict[str, Any] = {}

    def fake_get(url: str, **kwargs: Any) -> FakeResponse:
        captured["url"] = url
        captured["headers"] = kwargs.get("headers")
        return FakeResponse()

    monkeypatch.setattr(handlers.httpx, "get", fake_get)
    files = [{"name": "borrador.md", "url_private": "https://files.slack.com/abc"}]

    reviewer_env["reviewer"].handle(
        _event("", files=files), reviewer_env["say"], reviewer_env["client"]
    )

    assert captured["url"] == "https://files.slack.com/abc"
    assert captured["headers"]["Authorization"] == "Bearer xoxb-test"
    assert reviewer_env["engine"].drafts[0].source == "borrador.md"


def test_unsupported_attachment_warns(reviewer_env: dict[str, Any]) -> None:
    files = [{"name": "imagen.png", "url_private": "https://files.slack.com/img"}]

    reviewer_env["reviewer"].handle(
        _event("", files=files), reviewer_env["say"], reviewer_env["client"]
    )

    assert "⚠️" in reviewer_env["say"].calls[0]["text"]
    assert reviewer_env["engine"].drafts == []


def test_review_errors_are_reported_to_user(
    reviewer_env: dict[str, Any], sample_draft_text: str
) -> None:
    def boom(draft: Any) -> ReviewResult:
        raise ValueError("borrador demasiado corto")

    reviewer_env["engine"].review = boom  # type: ignore[method-assign]

    reviewer_env["reviewer"].handle(
        _event(sample_draft_text), reviewer_env["say"], reviewer_env["client"]
    )

    last_message = reviewer_env["say"].calls[-1]["text"]
    assert "No pude completar la revisión" in last_message


def test_replies_stay_in_thread(reviewer_env: dict[str, Any], sample_draft_text: str) -> None:
    event = _event(sample_draft_text)
    event["thread_ts"] = "000.111"

    reviewer_env["reviewer"].handle(event, reviewer_env["say"], reviewer_env["client"])

    assert all(call["thread_ts"] == "000.111" for call in reviewer_env["say"].calls)
    assert reviewer_env["client"].uploads[0]["thread_ts"] == "000.111"
