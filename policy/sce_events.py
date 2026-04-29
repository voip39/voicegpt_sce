from datetime import datetime, timezone


def _now_ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_policy_check_event(state, decision: dict, policy_decision: dict) -> dict:
    skill_request = decision.get("skill_request", {}) or {}
    skill_name = skill_request.get("skill_name")

    return {
        "sce_version": "2.0",
        "event": {
            "id": f"policycheck-{state.thread_id}-{state.session_id}-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            "kind": "policy_check",
            "action": "evaluated",
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
            "skill_name": skill_name,
            "allowed": policy_decision.get("allowed"),
            "reason": policy_decision.get("reason"),
            "policy_code": policy_decision.get("policy_code"),
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
                "emitted_by": "policy_layer",
            },
        },
    }


def build_policy_block_event(state, decision: dict, policy_decision: dict) -> dict:
    skill_request = decision.get("skill_request", {}) or {}
    skill_name = skill_request.get("skill_name")
    arguments = skill_request.get("arguments", {}) or {}

    return {
        "sce_version": "2.0",
        "event": {
            "id": f"policyblock-{state.thread_id}-{state.session_id}-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            "kind": "policy_block",
            "action": "blocked",
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
            "skill_name": skill_name,
            "arguments": arguments,
            "reason": policy_decision.get("reason"),
            "policy_code": policy_decision.get("policy_code"),
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
                "emitted_by": "policy_layer",
            },
        },
    }
