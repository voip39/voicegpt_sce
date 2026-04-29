from __future__ import annotations

from typing import Any, Dict, List, Optional


ALLOWED_DECISION_TYPES = {
    # Phase 9
    "answer",
    "clarify",
    "confirm",
    "action",
    "error",

    # Phase 11
    "greeting",
    "memory_write_ack",
    "profile_summary",
    "memory_recall",
    "continuity_recall",
    "conversation_summary",

    # Phase 16
    "handoff",
}


ALLOWED_STATE_PATCH_KEYS = {
    "last_user_message",
    "last_agent_reply",
}


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _fallback_reply(agent_type: str) -> str:
    normalized = str(agent_type).upper()

    if normalized == "VIP":
        return "Hello, this is your personal assistant. How can I help you? I'm sorry, but I couldn't complete that response safely."

    if normalized == "FRONTDESK":
        return "Hello, thank you for calling. How can I help you today? I'm sorry, but I couldn't complete that response safely."

    return "Hello. I'm sorry, but I couldn't complete that response safely."


def _normalize_reply(reply: Any, agent_type: str) -> str:
    normalized = _safe_str(reply)
    if normalized:
        return normalized
    return _fallback_reply(agent_type)


def _normalize_decision_type(decision_type: Any) -> str:
    value = _safe_str(decision_type).lower()
    if value in ALLOWED_DECISION_TYPES:
        return value
    return "error"


def _filter_state_patch(state_patch: Any) -> Dict[str, Any]:
    patch = _safe_dict(state_patch)
    return {k: patch[k] for k in ALLOWED_STATE_PATCH_KEYS if k in patch}


def _normalize_execution_trace(execution_trace: Any) -> Dict[str, Any]:
    trace = _safe_dict(execution_trace)

    normalized: Dict[str, Any] = {}

    if "strategy" in trace:
        normalized["strategy"] = _safe_str(trace["strategy"])

    if "selected_path" in trace:
        normalized["selected_path"] = _safe_str(trace["selected_path"])

    if "signals" in trace and isinstance(trace["signals"], dict):
        normalized["signals"] = trace["signals"]

    if "notes" in trace:
        if isinstance(trace["notes"], list):
            normalized["notes"] = [str(x) for x in trace["notes"]]
        else:
            normalized["notes"] = [_safe_str(trace["notes"])]

    if "decision" in trace and isinstance(trace["decision"], dict):
        normalized["decision"] = trace["decision"]

    if "outcome" in trace and isinstance(trace["outcome"], dict):
        normalized["outcome"] = trace["outcome"]

    if "render" in trace and isinstance(trace["render"], dict):
        normalized["render"] = trace["render"]

    if "office" in trace and isinstance(trace["office"], dict):
        normalized["office"] = trace["office"]

    return normalized


def _normalize_observations(observations: Any) -> List[Any]:
    return _safe_list(observations)


def apply_outcome_guardrails(
    outcome: Dict[str, Any],
    tenant_ctx: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    raw = _safe_dict(outcome)
    tenant = _safe_dict(tenant_ctx)

    agent_type = _safe_str(
        raw.get("agent_type") or tenant.get("agent_type") or "FRONTDESK"
    ) or "FRONTDESK"

    original_decision_type = raw.get("decision_type")

    normalized_decision_type = _normalize_decision_type(original_decision_type)
    normalized_reply = _normalize_reply(raw.get("reply"), agent_type)
    filtered_state_patch = _filter_state_patch(raw.get("state_patch"))

    normalized_execution_trace = _normalize_execution_trace(raw.get("execution_trace"))
    normalized_observations = _normalize_observations(raw.get("observations"))

    decision_type_valid = normalized_decision_type == _safe_str(original_decision_type).lower()

    notes: List[str] = []

    if not decision_type_valid:
        notes.append("decision_type_normalized")

    guarded_outcome: Dict[str, Any] = {
        "ok": bool(raw.get("ok", True)),
        "agent_type": agent_type,
        "decision_type": normalized_decision_type,
        "reply": normalized_reply,
        "profile_used": bool(raw.get("profile_used", False)),
        "memory_used": bool(raw.get("memory_used", False)),
        "execution_trace": normalized_execution_trace,
        "observations": normalized_observations,
        "state_patch": filtered_state_patch,
        "guardrail_trace": {
            "applied": True,
            "decision_type_valid": decision_type_valid,
            "reply_normalized": False,
            "state_patch_filtered": filtered_state_patch != _safe_dict(raw.get("state_patch")),
            "notes": notes,
        },
    }

    return guarded_outcome