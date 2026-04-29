from __future__ import annotations

from typing import Any, Dict

from policy.outcome_guardrails import apply_outcome_guardrails
from runtime.agent_outcome import build_agent_outcome
from runtime.decision_producer import get_decision_producer
from runtime.decision_router import route_decision
from runtime.office.router import route_office_handoff
from runtime.outcome_builder import build_outcome_from_reply
from runtime.renderers.selector import render_outcome_for_channel


def handle_runtime_context(runtime_ctx: Dict[str, Any]) -> Dict[str, Any]:
    tenant = runtime_ctx.get("tenant") or {}
    agent_type = tenant.get("agent_type") or "FRONTDESK"

    text = ((runtime_ctx.get("current_turn") or {}).get("text") or "").strip()
    channel = "web"

    routing = route_decision(text)

    producer = get_decision_producer()
    decision = producer.produce(runtime_ctx, routing)

    decision = _apply_frontdesk_bridge(decision, text)

    execution = _execute_decision(decision)

    outcome_obj = build_outcome_from_reply(
        execution["reply"],
        decision_type=decision.decision_type,
    )

    render = render_outcome_for_channel(outcome_obj, channel)

    office_trace = {
        "target_office": decision.target_office,
        "handoff_candidate": decision.decision_type == "handoff",
        "handoff_reason": decision.handoff_reason,
        "office_execution": execution.get("office_execution"),
    }

    outcome = build_agent_outcome(
        agent_type=agent_type,
        reply=render.text,
        decision_type=decision.decision_type,
        profile_used=False,
        memory_used=False,
        execution_trace={
            "decision": decision.to_dict(),
            "office": office_trace,
        },
        observations=[],
        state_patch={},
    )

    return apply_outcome_guardrails(outcome)


def _apply_frontdesk_bridge(decision: Any, text: str):
    t = text.lower()

    if "human" in t:
        decision.decision_type = "handoff"
        decision.target_office = "HUMAN_DESK"
        decision.handoff_reason = "human_request"

    elif any(x in t for x in ["pay", "invoice", "bill"]):
        decision.decision_type = "handoff"
        decision.target_office = "BILLING"
        decision.handoff_reason = "billing_intent"

    elif any(x in t for x in ["service", "pricing", "interested"]):
        decision.decision_type = "handoff"
        decision.target_office = "SALES"
        decision.handoff_reason = "sales_intent"

    else:
        decision.target_office = "FRONTDESK"
        decision.handoff_reason = None

    return decision


def _execute_decision(decision: Any) -> Dict[str, Any]:
    if decision.decision_type == "handoff":
        return route_office_handoff(decision)

    return {"reply": "Could you clarify your request?"}