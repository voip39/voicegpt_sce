from __future__ import annotations

from runtime.outcome import OutcomeObject


def build_outcome_from_reply(
    reply: str,
    *,
    decision_type: str,
    template_family: str | None = None,
) -> OutcomeObject:
    return OutcomeObject(
        text=reply,
        short_text=_build_short(reply),
        speech_text=_build_speech(reply),
        outcome_type=decision_type,
        template_family=template_family,
        meta={"source": "builder_v13"},
    )


def _build_short(text: str) -> str:
    source = (text or "").strip()
    if not source:
        return ""

    if len(source) <= 160:
        return source

    return source[:157].rstrip() + "..."


def _build_speech(text: str) -> str:
    return (text or "").strip()