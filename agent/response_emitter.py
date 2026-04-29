from datetime import datetime, timezone
from agent.agent_state import AgentState


def emit_response_event(state: AgentState, decision: dict) -> dict | None:
    """
    Преобразует decision в новое SCE response event.
    Если response нет, возвращает None.

    Поддерживает:
    - action="respond"
    - action="call_skill" + response bridge
    """

    response = decision.get("response")
    if not response:
        return None

    action = decision.get("action")
    if action not in {"respond", "call_skill"}:
        return None

    event_id = f"resp-{state.thread_id}-{state.session_id}-{int(datetime.now(timezone.utc).timestamp())}"
    now_ts = datetime.now(timezone.utc).isoformat()

    return {
        "sce_version": "2.0",
        "event": {
            "id": event_id,
            "kind": "message",
            "action": "responded",
            "direction": "outbound",
            "ts": now_ts,
        },
        "subject": {
            "type": state.subject_type,
            "subject_id": state.subject_id,
        },
        "content": {
            "modality": response.get("type", "text"),
            "attachments": [],
            "text": response.get("text"),
        },
        "route": {
            "channel_family": "agent",
        },
        "context": {
            "tenant_id": state.tenant_id,
            "tenant_kind": state.tenant_kind,
            "thread_id": state.thread_id,
            "session_id": state.session_id,
        },
        "meta": {
            "schema_version": "2.0",
            "extensions": {
                "emitted_by": "agent_runtime",
                "decision_action": action,
            },
        },
    }
