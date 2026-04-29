from typing import Dict, Any

from runtime.agent_state import load_state, save_state, append_history
from runtime.context_builder import build_runtime_context
from runtime.orchestrator import handle_runtime_context
from runtime.memory_bridge import recall_memory
from runtime.memory_writer import write_memory_if_detected

from core.tenant_profile_resolver import (
    resolve_tenant_profile_type,
    load_frontdesk_profile,
    load_vip_profile,
)


def handle_turn(event: Dict[str, Any]) -> Dict[str, Any]:
    route = event.get("route") or {}
    context = event.get("context") or {}
    subject = event.get("subject") or {}
    content = event.get("content") or {}

    tenant_id = route.get("tenant_id") or context.get("tenant_id")
    session_id = route.get("session_id") or context.get("session_id")
    thread_id = context.get("thread_id") or session_id
    subject_id = subject.get("subject_id") or "unknown"

    if tenant_id is None:
        return {"ok": False, "error": "missing_tenant_id"}

    tenant_id = int(tenant_id)

    agent_type = resolve_tenant_profile_type(tenant_id)

    if agent_type == "VIP":
        profile = load_vip_profile(tenant_id)
    else:
        profile = load_frontdesk_profile(tenant_id)

    state = load_state(tenant_id, thread_id, session_id, subject_id, agent_type)

    user_text = content.get("text") or ""

    # write simple facts into memory before recall
    write_memory_if_detected(
        tenant_id=tenant_id,
        subject_id=subject_id,
        text=user_text,
    )

    memory_items = recall_memory(tenant_id, subject_id, user_text)

    runtime_ctx = build_runtime_context(
        current_turn={
            "text": user_text,
            "event": event,
        },
        continuity_ctx={
            "state": state,
            "history": state.get("history") or [],
            "last_user_message": state.get("last_user_message"),
            "last_agent_reply": state.get("last_agent_reply"),
            "thread_id": thread_id,
            "session_id": session_id,
            "subject_id": subject_id,
        },
        memory_items=memory_items,
        tenant_ctx={
            "tenant_id": tenant_id,
            "agent_type": agent_type,
            "profile": profile,
        },
    )

    result = handle_runtime_context(runtime_ctx)

    reply = result.get("reply") or ""

    append_history(state, "user", user_text)
    append_history(state, "assistant", reply)

    state["last_user_message"] = user_text
    state["last_agent_reply"] = reply

    save_state(state)

    return result