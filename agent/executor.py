from __future__ import annotations

from typing import Any, Mapping


def _safe_dict(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    return {}


def _safe_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    return []


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def execute_plan(
    *,
    plan: Mapping[str, Any] | None,
    intent: str,
    strategy: Mapping[str, Any] | None,
    evidence: Mapping[str, Any] | None,
    response_text: str,
) -> dict[str, Any]:
    """
    Phase 7D / Execution v1

    Пока это не full skill orchestration.
    Это controlled execution trace layer:
    - принимает plan
    - фиксирует steps
    - возвращает execution metadata
    - оставляет текущий response_text неизменным
    """

    plan = _safe_dict(plan)
    strategy = _safe_dict(strategy)
    evidence = _safe_dict(evidence)

    steps = _safe_list(plan.get("steps"))
    mode = _safe_text(plan.get("mode")) or _safe_text(strategy.get("mode"))

    executed_steps: list[dict[str, Any]] = []

    for step in steps:
        step_name = _safe_text(step)
        if not step_name:
            continue

        executed_steps.append({
            "step": step_name,
            "status": "completed",
        })

    execution_trace = {
        "mode": mode,
        "intent": _safe_text(intent),
        "step_count": len(executed_steps),
        "steps": executed_steps,
        "evidence_summary": {
            "has_memory_result": evidence.get("memory_result") is not None,
            "has_ranking_trace": evidence.get("ranking_trace") is not None,
            "retrieved_count": len(_safe_list(evidence.get("retrieved_items"))),
            "ranked_count": len(_safe_list(evidence.get("ranked_items"))),
        },
    }

    return {
        "response_text": response_text,
        "execution_trace": execution_trace,
    }
