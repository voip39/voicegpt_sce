from __future__ import annotations

from collections.abc import Callable


def strip_terminal_punctuation(value: str) -> str:
    return (value or "").rstrip(" .!?")


# ---------- MEMORY ----------

def map_recall_body_to_sms_compact(body: str) -> str:
    source = (body or "").strip()
    if not source:
        return ""

    pairs = [
        ("Your favorite food is ", "Favorite food: "),
        ("Your favorite color is ", "Favorite color: "),
        ("Your name is ", "Name: "),
    ]

    for prefix, compact in pairs:
        if source.startswith(prefix):
            value = strip_terminal_punctuation(source[len(prefix):].strip())
            if value:
                return f"{compact}{value}."

    return source


def map_recall_body_to_voice_natural(body: str) -> str:
    return (body or "").strip()


def map_memory_write_body_to_sms(body: str) -> str:
    source = (body or "").strip()
    if not source:
        return ""

    pairs = [
        ("Got it — I'll remember that your favorite food is ", "Saved: favorite food = "),
        ("Got it — I'll remember that your favorite color is ", "Saved: favorite color = "),
        ("Got it — I'll remember that your name is ", "Saved: name = "),
    ]

    for prefix, compact in pairs:
        if source.startswith(prefix):
            value = strip_terminal_punctuation(source[len(prefix):].strip())
            if value:
                return f"{compact}{value}."

    if source == "Got it — I'll remember that.":
        return "Saved."

    return source


def map_memory_write_body_to_voice(body: str) -> str:
    source = (body or "").strip()
    if not source:
        return ""

    pairs = [
        ("Got it — I'll remember that your favorite food is ", "Got it. I'll remember your favorite food is "),
        ("Got it — I'll remember that your favorite color is ", "Got it. I'll remember your favorite color is "),
        ("Got it — I'll remember that your name is ", "Got it. I'll remember your name is "),
    ]

    for prefix, spoken in pairs:
        if source.startswith(prefix):
            value = strip_terminal_punctuation(source[len(prefix):].strip())
            if value:
                return f"{spoken}{value}."

    if source == "Got it — I'll remember that.":
        return "Got it. I'll remember that."

    return source


# ---------- PREVIOUS MESSAGE ----------

def map_previous_message_to_sms_compact(body: str) -> str:
    source = (body or "").strip()
    if not source:
        return ""

    if source == "I don't have a previous message yet.":
        return "No previous message yet."

    pairs = [
        ("Your previous message was: ", "Previous msg: "),
        ("The previous message was: ", "Previous msg: "),
    ]

    for prefix, compact in pairs:
        if source.startswith(prefix):
            value = strip_terminal_punctuation(source[len(prefix):].strip())
            if value:
                return f"{compact}{value}."

    return source


def map_previous_message_to_voice_natural(body: str) -> str:
    return (body or "").strip()


# ---------- PROFILE SUMMARY ----------

def map_profile_summary_to_sms_compact(body: str) -> str:
    source = (body or "").strip()
    if not source:
        return ""

    if source.lower().startswith("here's what i know about you:"):
        source = source.split(":", 1)[1].strip()

    source = source.replace("favorite ", "")
    source = source.replace(" is ", "=")

    return f"Profile: {source}"


def map_profile_summary_to_voice_natural(body: str) -> str:
    source = (body or "").strip()
    if not source:
        return ""

    if source.lower().startswith("here's what i know about you:"):
        return source

    return f"Here's what I know about you: {source}"


# ---------- CONVERSATION SUMMARY ----------

def map_conversation_summary_to_sms_compact(body: str) -> str:
    source = (body or "").strip()
    if not source:
        return ""

    if source.lower().startswith("summary:"):
        source = source.split(":", 1)[1].strip()

    if len(source) > 120:
        source = source[:117].rstrip() + "..."

    return f"Summary: {source}"


def map_conversation_summary_to_voice_natural(body: str) -> str:
    source = (body or "").strip()
    if not source:
        return ""

    if len(source) > 300:
        source = source[:297].rstrip() + "..."

    return source


# ---------- REGISTRIES ----------

RenderPolicyFn = Callable[[str], str]
RenderPolicyEntry = tuple[RenderPolicyFn, str]

SMS_POLICY_REGISTRY: dict[str, RenderPolicyEntry] = {
    "memory_recall":        (map_recall_body_to_sms_compact,           "memory_recall_compact"),
    "memory_write":         (map_memory_write_body_to_sms,             "memory_write_ack_compact"),
    "memory_write_ack":     (map_memory_write_body_to_sms,             "memory_write_ack_compact"),
    "previous_message":     (map_previous_message_to_sms_compact,      "previous_message_compact"),
    "profile_summary":      (map_profile_summary_to_sms_compact,       "profile_summary_compact"),
    "conversation_summary": (map_conversation_summary_to_sms_compact,  "conversation_summary_compact"),
}

VOICE_POLICY_REGISTRY: dict[str, RenderPolicyEntry] = {
    "memory_recall":        (map_recall_body_to_voice_natural,         "memory_recall_voice"),
    "memory_write":         (map_memory_write_body_to_voice,           "memory_write_voice"),
    "memory_write_ack":     (map_memory_write_body_to_voice,           "memory_write_voice"),
    "previous_message":     (map_previous_message_to_voice_natural,    "previous_message_voice"),
    "profile_summary":      (map_profile_summary_to_voice_natural,     "profile_summary_voice"),
    "conversation_summary": (map_conversation_summary_to_voice_natural,"conversation_summary_voice"),
}