from typing import Any


def synthesize_previous_message(value: Any) -> str:
    text = _clean(value)
    if not text:
        return "I don’t have a previous message yet."
    return f"Previously, you said: “{text}”."


def synthesize_history_summary(value: Any) -> str:
    text = _clean(value)
    if not text:
        return "I don’t have any conversation history yet."
    return f"Here’s a short summary of our conversation so far: {text}."


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().strip(".").strip()