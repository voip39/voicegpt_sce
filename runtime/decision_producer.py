from __future__ import annotations

import logging
import os
import traceback
from typing import Any, Dict, Optional, Protocol, runtime_checkable

from runtime.decision_builder import (
    DecisionObject,
    InputsMap,
    build_decision,
    build_decision_object,
)
from runtime.llm_decision.validator import ValidationResult


logger = logging.getLogger("llm_decision")


@runtime_checkable
class DecisionProducer(Protocol):
    def produce(self, runtime_ctx: Dict[str, Any], routing: Dict[str, Any]) -> DecisionObject:
        ...


class DeterministicDecisionProducer:
    def produce(self, runtime_ctx: Dict[str, Any], routing: Dict[str, Any]) -> DecisionObject:
        return build_decision(runtime_ctx, routing)


class LLMDecisionProducer:
    def __init__(self) -> None:
        self._fallback = DeterministicDecisionProducer()

    def produce(self, runtime_ctx: Dict[str, Any], routing: Dict[str, Any]) -> DecisionObject:
        try:
            from runtime.llm_decision.prompt_builder import build_decision_prompts
            from runtime.llm_decision.provider import generate_decision_json
            from runtime.llm_decision.response_parser import parse_llm_decision_response
            from runtime.llm_decision.validator import validate_decision_request

            system_prompt, user_prompt = build_decision_prompts(runtime_ctx, routing)
            llm_data = generate_decision_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            llm_request = parse_llm_decision_response(
                llm_data,
                runtime_ctx=runtime_ctx,
                routing=routing,
            )

            is_valid, reasons = validate_decision_request(llm_request)
            if not is_valid:
                logger.warning(
                    "llm_decision invalid, fallback to deterministic: reasons=%s",
                    reasons,
                )
                return self._fallback.produce(runtime_ctx, routing)

            llm_obj = build_decision_object(llm_request)
            llm_obj = _hydrate_payload(llm_obj, runtime_ctx)
            return llm_obj

        except Exception as e:
            logger.warning("llm_decision fallback to deterministic: %s", e)
            return self._fallback.produce(runtime_ctx, routing)


class ShadowDecisionProducer:
    def __init__(self) -> None:
        self._deterministic = DeterministicDecisionProducer()

    def produce(self, runtime_ctx: Dict[str, Any], routing: Dict[str, Any]) -> DecisionObject:
        det_decision = self._deterministic.produce(runtime_ctx, routing)

        llm_decision: Optional[DecisionObject] = None
        validation_result: Optional[ValidationResult] = None
        llm_error: Optional[str] = None

        try:
            from runtime.llm_decision.prompt_builder import build_decision_prompts
            from runtime.llm_decision.provider import generate_decision_json
            from runtime.llm_decision.response_parser import parse_llm_decision_response
            from runtime.llm_decision.validator import validate_decision_request
            from runtime.llm_decision.shadow_logger import log_shadow_decision

            system_prompt, user_prompt = build_decision_prompts(runtime_ctx, routing)
            llm_data = generate_decision_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            llm_request = parse_llm_decision_response(
                llm_data,
                runtime_ctx=runtime_ctx,
                routing=routing,
            )
            validation_result = validate_decision_request(llm_request)

            is_valid, _reasons = validation_result
            if is_valid:
                llm_decision = build_decision_object(llm_request)

            try:
                log_shadow_decision(
                    runtime_ctx=runtime_ctx,
                    deterministic_decision=det_decision,
                    llm_decision=llm_decision,
                    validation_result=validation_result,
                    llm_error=llm_error,
                )
            except Exception as e:
                logger.warning("shadow logging failed: %s", e)

        except Exception:
            llm_error = traceback.format_exc(limit=5)

            try:
                from runtime.llm_decision.shadow_logger import log_shadow_decision

                log_shadow_decision(
                    runtime_ctx=runtime_ctx,
                    deterministic_decision=det_decision,
                    llm_decision=None,
                    validation_result=None,
                    llm_error=llm_error,
                )
            except Exception as e:
                logger.warning("shadow logging failed after llm error: %s", e)

        return det_decision


def _hydrate_payload(
    decision: DecisionObject,
    runtime_ctx: Dict[str, Any],
) -> DecisionObject:
    """
    Hydrates execution-ready payload for an LLM-produced decision by using the
    deterministic builder for the same routing/capability path.

    LLM decides WHAT.
    Deterministic builder hydrates HOW.
    """
    routing = {
        "route": decision.route,
        "family": decision.route_family,
        "matched_by": decision.matched_by,
        "priority": decision.priority,
        "capability": decision.capability,
    }

    det = build_decision(runtime_ctx, routing)

    original_payload = dict(decision.payload or {})
    hydrated_payload = dict(det.payload or {})

    hydrated_payload["llm_semantic_draft"] = original_payload.get("llm_semantic_draft", {})
    hydrated_payload["hydrated_from_deterministic"] = True

    decision.payload = hydrated_payload
    decision.inputs_used = InputsMap(
        profile=det.inputs_used.profile,
        memory=det.inputs_used.memory,
        history=det.inputs_used.history,
    )

    return decision


def get_decision_producer() -> DecisionProducer:
    mode = (os.getenv("DECISION_PRODUCER_MODE") or "deterministic").strip().lower()

    if mode == "live":
        return LLMDecisionProducer()

    if mode == "shadow":
        return ShadowDecisionProducer()

    return DeterministicDecisionProducer()