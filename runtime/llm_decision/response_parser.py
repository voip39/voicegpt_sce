from __future__ import annotations

from typing import Any, Dict, List

from runtime.decision_builder import (
    DecisionRequest,
    InputsMap,
    NoteEntry,
    ResolverInfo,
    ResponsePlan,
    SynthesisInfo,
)


ALLOWED_DECISION_TYPES = {
    "greeting",
    "profile_summary",
    "memory_write_ack",
    "memory_recall",
    "continuity_recall",
    "conversation_summary",
    "answer",
}

ALLOWED_CAPABILITIES = {
    "greeting",
    "profile_summary",
    "memory_write",
    "name_recall",
    "favorite_color_recall",
    "favorite_food_recall",
    "previous_message",
    "conversation_summary",
    "answer",
}

ALLOWED_RESPONSE_STYLES = {
    "direct",
}


def parse_llm_decision_response(
    llm_data: Dict[str, Any],
    *,
    runtime_ctx: Dict[str, Any],
    routing: Dict[str, Any],
) -> DecisionRequest:
    """
    Parses a minimal Variant B LLM decision draft and converts it into a canonical
    DecisionRequest using known deterministic metadata from runtime_ctx + routing.

    LLM is allowed to provide only semantic decision fields.
    Canonical lineage and runtime-known fields are filled here.

    In 12D-start, resolver and synthesis execution semantics remain deterministic-only,
    so this parser sets them to used=False intentionally.
    """
    profile = runtime_ctx.get("profile") or {}
    memory_items = (runtime_ctx.get("memory") or {}).get("items") or []
    history = (runtime_ctx.get("continuity") or {}).get("history") or []
    text = ((runtime_ctx.get("current_turn") or {}).get("text") or "").strip()

    route = str(routing.get("route", "default_answer"))
    route_family = str(routing.get("family", "fallback"))
    matched_by = str(routing.get("matched_by", "llm_producer"))
    priority = int(routing.get("priority", 10))
    routed_capability = str(routing.get("capability") or "answer")

    inputs_available = InputsMap(
        profile=bool(profile),
        memory=bool(memory_items),
        history=bool(history),
    )

    decision_type = _normalize_decision_type(llm_data.get("decision_type"))
    capability = _normalize_capability(llm_data.get("capability"), fallback=routed_capability)
    selected_path = _normalize_selected_path(
        llm_data.get("selected_path"),
        fallback=f"llm_{capability}",
    )

    inputs_used = _parse_inputs_used(llm_data.get("inputs_used"), inputs_available)

    response_plan = _parse_response_plan(llm_data.get("response_plan"), capability=capability)

    confidence = _parse_confidence(llm_data.get("confidence"))

    notes = _parse_notes(llm_data.get("notes"))
    notes.insert(
        0,
        NoteEntry(
            source="builder",
            kind="info",
            text="decision request parsed from llm semantic draft",
        ),
    )

    return DecisionRequest(
        decision_type=decision_type,
        capability=capability,
        selected_path=selected_path,
        route=route,
        route_family=route_family,
        matched_by=matched_by,
        priority=priority,
        inputs_available=inputs_available,
        inputs_used=inputs_used,
        resolver=ResolverInfo(
            used=False,
            name=None,
            source=None,
            found=False,
        ),
        synthesis=SynthesisInfo(
            used=False,
            name=None,
        ),
        response_plan=response_plan,
        notes=notes,
        decision_mode="llm_assisted",
        confidence=confidence,
        payload={
            "llm_semantic_draft": _safe_dict(llm_data),
            "text": text,
        },
    )


def _normalize_decision_type(value: Any) -> str:
    text = _safe_str(value).lower()
    if text in ALLOWED_DECISION_TYPES:
        return text
    return "answer"


def _normalize_capability(value: Any, *, fallback: str) -> str:
    text = _safe_str(value)
    if text in ALLOWED_CAPABILITIES:
        return text
    if fallback in ALLOWED_CAPABILITIES:
        return fallback
    return "answer"


def _normalize_selected_path(value: Any, *, fallback: str) -> str:
    text = _safe_str(value)
    return text or fallback


def _parse_inputs_used(value: Any, inputs_available: InputsMap) -> InputsMap:
    data = _safe_dict(value)

    requested_profile = bool(data.get("profile", False))
    requested_memory = bool(data.get("memory", False))
    requested_history = bool(data.get("history", False))

    return InputsMap(
        profile=requested_profile and inputs_available.profile,
        memory=requested_memory and inputs_available.memory,
        history=requested_history and inputs_available.history,
    )


def _parse_response_plan(value: Any, *, capability: str) -> ResponsePlan:
    data = _safe_dict(value)

    response_style = _safe_str(data.get("response_style")) or "direct"
    if response_style not in ALLOWED_RESPONSE_STYLES:
        response_style = "direct"

    template_family = _safe_str(data.get("template_family")) or _default_template_family(capability)
    template_family = _normalize_template_family(template_family, capability)

    return ResponsePlan(
        response_style=response_style,
        template_family=template_family,
    )


def _normalize_template_family(template_family: str, capability: str) -> str:
    """
    Normalizes common LLM aliases to canonical template_family values.
    Falls back to capability-derived default if alias not recognized.
    """
    aliases = {
        "summary": "conversation_summary",
        "conversation": "conversation_summary",
        "history_summary": "conversation_summary",
        "continuity": "continuity_recall",
        "previous": "continuity_recall",
        "recall": "memory_recall",
        "memory": "memory_recall",
        "profile": "profile_summary",
        "write_ack": "memory_write_ack",
        "ack": "memory_write_ack",
        "favorite_food": "memory_recall",
        "favorite_color": "memory_recall",
    }

    normalized = aliases.get(template_family)
    if normalized:
        return normalized

    canonical = {
        "greeting",
        "profile_summary",
        "memory_write_ack",
        "memory_recall",
        "continuity_recall",
        "conversation_summary",
        "answer",
    }

    if template_family in canonical:
        return template_family

    return _default_template_family(capability)


def _default_template_family(capability: str) -> str:
    if capability == "greeting":
        return "greeting"
    if capability == "profile_summary":
        return "profile_summary"
    if capability == "memory_write":
        return "memory_write_ack"
    if capability in {"name_recall", "favorite_color_recall", "favorite_food_recall"}:
        return "memory_recall"
    if capability == "previous_message":
        return "continuity_recall"
    if capability == "conversation_summary":
        return "conversation_summary"
    return "answer"


def _parse_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except Exception:
        return 0.5

    if confidence < 0.0:
        return 0.0
    if confidence > 1.0:
        return 1.0
    return confidence


def _parse_notes(value: Any) -> List[NoteEntry]:
    notes: List[NoteEntry] = []

    if not isinstance(value, list):
        return notes

    for item in value:
        if not isinstance(item, dict):
            continue

        source = _normalize_note_source(item.get("source"))
        kind = _normalize_note_kind(item.get("kind"))
        text = _safe_str(item.get("text"))

        if not text:
            continue

        notes.append(
            NoteEntry(
                source=source,
                kind=kind,
                text=text,
            )
        )

    return notes


def _normalize_note_source(value: Any) -> str:
    text = _safe_str(value).lower()
    if text in {"router", "resolver", "synthesis", "builder"}:
        return text
    return "builder"


def _normalize_note_kind(value: Any) -> str:
    text = _safe_str(value).lower()
    if text in {"match", "fallback", "empty", "info"}:
        return text
    return "info"


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()