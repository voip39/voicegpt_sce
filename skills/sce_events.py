from datetime import datetime, timezone


def _now_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_tool_call_event(state, invocation, skill_request: dict) -> dict:
    return {
        "sce_version": "2.0",
        "event": {
            "id": f"toolcall-{invocation.invocation_id}",
            "kind": "tool_call",
            "action": "requested",
            "direction": "internal",
            "ts": _now_ts(),
        },
        "subject": {
            "type": state.subject_type,
            "subject_id": state.subject_id,
        },
        "content": {
            "modality": "json",
            "attachments": [],
            "text": None,
            "tool_name": invocation.skill_name,
            "arguments": skill_request.get("arguments", {}) or {},
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
                "emitted_by": "skill_runtime",
                "invocation_id": invocation.invocation_id,
            },
        },
    }


def build_tool_result_event(state, invocation, skill_result: dict) -> dict:
    return {
        "sce_version": "2.0",
        "event": {
            "id": f"toolresult-{invocation.invocation_id}",
            "kind": "tool_result",
            "action": "completed",
            "direction": "internal",
            "ts": _now_ts(),
        },
        "subject": {
            "type": state.subject_type,
            "subject_id": state.subject_id,
        },
        "content": {
            "modality": "json",
            "attachments": [],
            "text": None,
            "tool_name": invocation.skill_name,
            "status": skill_result.get("status"),
            "result": skill_result.get("result"),
            "error_code": skill_result.get("error_code"),
            "error_message": skill_result.get("error_message"),
            "latency_ms": skill_result.get("latency_ms"),
            "side_effect_committed": skill_result.get("side_effect_committed"),
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
                "emitted_by": "skill_runtime",
                "invocation_id": invocation.invocation_id,
            },
        },
    }
