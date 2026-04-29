from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from runtime.decision_builder import DecisionObject
from runtime.llm_decision.validator import ValidationResult


logger = logging.getLogger("shadow_decision")

LLM_OUTCOME_MATCHED = "matched"
LLM_OUTCOME_DIVERGED = "diverged"
LLM_OUTCOME_LOW_CONFIDENCE = "low_confidence"
LLM_OUTCOME_INVALID = "invalid"
LLM_OUTCOME_FAILED = "failed"


def log_shadow_decision(
    *,
    runtime_ctx: Dict[str, Any],
    deterministic_decision: DecisionObject,
    llm_decision: Optional[DecisionObject],
    validation_result: Optional[ValidationResult] = None,
    llm_error: Optional[str] = None,
) -> None:
    """
    Logs deterministic vs LLM decision comparison for shadow mode.

    This logger must never break production flow.
    Any internal logger error is swallowed and emitted as warning.
    """
    try:
        text = ((runtime_ctx.get("current_turn") or {}).get("text") or "").strip()

        tenant_id = _extract_tenant_id(runtime_ctx)
        session_id = _extract_session_id(runtime_ctx)

        outcome, divergence, reasons = _classify_shadow_outcome(
            deterministic_decision=deterministic_decision,
            llm_decision=llm_decision,
            validation_result=validation_result,
            llm_error=llm_error,
        )

        agreement = outcome == LLM_OUTCOME_MATCHED

        entry = {
            "tenant_id": tenant_id,
            "session_id": session_id,
            "producer_mode": "shadow",
            "agreement": agreement,
            "outcome": outcome,
            "reasons": reasons,
            "divergence": divergence,
            "user_text": text[:200],
            "deterministic": {
                "decision_type": deterministic_decision.decision_type,
                "capability": deterministic_decision.capability,
                "selected_path": deterministic_decision.selected_path,
                "confidence": deterministic_decision.confidence,
            },
            "llm": _serialize_llm_decision(llm_decision),
            "llm_error": _serialize_llm_error(llm_error),
        }

        logger.warning("shadow_decision %s", entry)

    except Exception as e:
        logger.warning("shadow_decision logger failure: %s", e)


def _classify_shadow_outcome(
    *,
    deterministic_decision: DecisionObject,
    llm_decision: Optional[DecisionObject],
    validation_result: Optional[ValidationResult],
    llm_error: Optional[str],
) -> tuple[str, Dict[str, Any], list[str]]:
    if llm_error:
        return LLM_OUTCOME_FAILED, {}, ["llm_provider_failed"]

    if llm_decision is None:
        return LLM_OUTCOME_FAILED, {}, ["llm_decision_missing"]

    if validation_result is not None:
        valid, reasons = validation_result
        if not valid:
            if "confidence_below_threshold" in reasons and len(reasons) == 1:
                return LLM_OUTCOME_LOW_CONFIDENCE, {}, reasons
            return LLM_OUTCOME_INVALID, {}, reasons

    divergence = _build_divergence(
        deterministic_decision=deterministic_decision,
        llm_decision=llm_decision,
    )

    if divergence:
        return LLM_OUTCOME_DIVERGED, divergence, []

    return LLM_OUTCOME_MATCHED, {}, []


def _build_divergence(
    *,
    deterministic_decision: DecisionObject,
    llm_decision: DecisionObject,
) -> Dict[str, Any]:
    divergence: Dict[str, Any] = {}

    if deterministic_decision.decision_type != llm_decision.decision_type:
        divergence["decision_type"] = {
            "deterministic": deterministic_decision.decision_type,
            "llm": llm_decision.decision_type,
        }

    if deterministic_decision.capability != llm_decision.capability:
        divergence["capability"] = {
            "deterministic": deterministic_decision.capability,
            "llm": llm_decision.capability,
        }

    return divergence


def _serialize_llm_decision(llm_decision: Optional[DecisionObject]) -> Optional[Dict[str, Any]]:
    if llm_decision is None:
        return None

    return {
        "decision_type": llm_decision.decision_type,
        "capability": llm_decision.capability,
        "selected_path": llm_decision.selected_path,
        "confidence": llm_decision.confidence,
    }


def _serialize_llm_error(llm_error: Optional[str]) -> Optional[Dict[str, str]]:
    if not llm_error:
        return None

    error_text = str(llm_error).strip()
    if not error_text:
        return None

    return {
        "error_type": "provider_error",
        "error_message": error_text[:300],
    }


def _extract_tenant_id(runtime_ctx: Dict[str, Any]) -> Any:
    event = (runtime_ctx.get("current_turn") or {}).get("event") or {}

    return (
        (event.get("route") or {}).get("tenant_id")
        or (event.get("context") or {}).get("tenant_id")
        or runtime_ctx.get("tenant_id")
        or (runtime_ctx.get("tenant") or {}).get("tenant_id")
        or "unknown"
    )


def _extract_session_id(runtime_ctx: Dict[str, Any]) -> str:
    event = (runtime_ctx.get("current_turn") or {}).get("event") or {}

    value = (
        (event.get("route") or {}).get("session_id")
        or (event.get("context") or {}).get("session_id")
        or runtime_ctx.get("session_id")
        or (runtime_ctx.get("tenant") or {}).get("session_id")
        or "unknown"
    )

    return str(value)