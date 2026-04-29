from __future__ import annotations

from runtime.outcome import OutcomeObject
from runtime.renderers.result import RenderResult
from runtime.renderers.sms_renderer import render_sms_outcome
from runtime.renderers.telegram_renderer import render_telegram_outcome
from runtime.renderers.voice_renderer import render_voice_outcome
from runtime.renderers.web_renderer import render_web_outcome


def render_outcome_for_channel(
    outcome: OutcomeObject,
    channel: str,
) -> RenderResult:
    normalized = (channel or "web").strip().lower()

    if normalized == "voice":
        return render_voice_outcome(outcome)

    if normalized == "sms":
        return render_sms_outcome(outcome)

    if normalized == "telegram":
        return render_telegram_outcome(outcome)

    return render_web_outcome(outcome)