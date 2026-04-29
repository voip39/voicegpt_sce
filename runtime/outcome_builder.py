from __future__ import annotations

from typing import Any, Dict

from runtime.outcome import OutcomeObject


def build_outcome_from_execution(
    execution: Dict[str, Any],
    *,
    decision_type: str,
    template_family: str | None = None,
) -> OutcomeObject:
    outcome_type = execution.get("outcome_type") or decision_type
    semantic = execution.get("semantic") or {}
    office_execution = execution.get("office_execution") or {}

    text = (
        execution.get("text")
        or execution.get("reply")
        or semantic.get("message")
        or _default_text_for_outcome(outcome_type, office_execution)
    )

    return OutcomeObject(
        text=text,
        short_text=_build_short(text),
        speech_text=_build_speech(text),
        outcome_type=outcome_type,
        template_family=template_family,
        channel_hints=execution.get("channel_hints") or {},
        meta={
            "source": "builder_v13_compat_v11",
            "semantic": semantic,
            "office_execution": office_execution,
            "legacy_reply_used": bool(execution.get("reply")),
        },
    )


def build_outcome_from_reply(
    reply: str,
    *,
    decision_type: str,
    template_family: str | None = None,
) -> OutcomeObject:
    return build_outcome_from_execution(
        {
            "reply": reply,
            "outcome_type": decision_type,
            "semantic": {"message": reply},
        },
        decision_type=decision_type,
        template_family=template_family,
    )


def _default_text_for_outcome(
    outcome_type: str,
    office_execution: Dict[str, Any],
) -> str:
    target = office_execution.get("target") or "FRONTDESK"

    if outcome_type == "handoff":
        return f"I routed your request to {target}."

    if outcome_type == "clarify":
        return "Could you clarify your request?"

    return "I processed your request."


def _build_short(text: str) -> str:
    source = (text or "").strip()
    if not source:
        return ""

    if len(source) <= 160:
        return source

    return source[:157].rstrip() + "..."


def _build_speech(text: str) -> str:
    return (text or "").strip()
