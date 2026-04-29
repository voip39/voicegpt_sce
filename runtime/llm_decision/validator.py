from __future__ import annotations

from typing import List, Tuple

from runtime.decision_builder import DecisionRequest


ValidationResult = Tuple[bool, List[str]]

CONFIDENCE_THRESHOLD = 0.5

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

DECISION_CAPABILITY_MAP = {
    "greeting": {"greeting"},
    "profile_summary": {"profile_summary"},
    "memory_write_ack": {"memory_write"},
    "memory_recall": {"name_recall", "favorite_color_recall", "favorite_food_recall"},
    "continuity_recall": {"previous_message"},
    "conversation_summary": {"conversation_summary"},
    "answer": {"answer"},
}


def validate_decision_request(req: DecisionRequest) -> ValidationResult:
    """
    Validates an LLM-produced DecisionRequest before execution.

    Returns:
        (is_valid, reasons)

    reasons contains machine-friendly validation tags for:
    - shadow logging
    - debugging
    - fallback explanations
    """
    reasons: List[str] = []

    # 1. decision_type vocabulary
    if req.decision_type not in ALLOWED_DECISION_TYPES:
        reasons.append("invalid_decision_type")

    # 2. capability vocabulary
    if req.capability not in ALLOWED_CAPABILITIES:
        reasons.append("invalid_capability")

    # 3. decision_type <-> capability semantic consistency
    if req.decision_type in ALLOWED_DECISION_TYPES:
        allowed_capabilities = DECISION_CAPABILITY_MAP.get(req.decision_type, set())
        if req.capability not in allowed_capabilities:
            reasons.append("decision_capability_mismatch")

    # 4. selected_path required
    if not isinstance(req.selected_path, str) or not req.selected_path.strip():
        reasons.append("missing_selected_path")

    # 5. confidence threshold and range
    if not isinstance(req.confidence, (int, float)):
        reasons.append("invalid_confidence_type")
    else:
        if req.confidence < CONFIDENCE_THRESHOLD:
            reasons.append("confidence_below_threshold")
        if req.confidence < 0.0 or req.confidence > 1.0:
            reasons.append("confidence_out_of_range")

    # 6. inputs_used must not exceed inputs_available
    if req.inputs_used.profile and not req.inputs_available.profile:
        reasons.append("profile_used_without_availability")

    if req.inputs_used.memory and not req.inputs_available.memory:
        reasons.append("memory_used_without_availability")

    if req.inputs_used.history and not req.inputs_available.history:
        reasons.append("history_used_without_availability")

    # 7. response_plan contract
    if req.response_plan.response_style != "direct":
        reasons.append("invalid_response_style")

    if not isinstance(req.response_plan.template_family, str) or not req.response_plan.template_family.strip():
        reasons.append("missing_template_family")

    # 8. notes shape
    if not isinstance(req.notes, list):
        reasons.append("notes_not_list")
    else:
        for note in req.notes:
            if not hasattr(note, "source") or not hasattr(note, "kind") or not hasattr(note, "text"):
                reasons.append("invalid_note_shape")
                break

    # 9. 12D-start invariant: validator accepts only llm_assisted requests
    if req.decision_mode != "llm_assisted":
        reasons.append("unexpected_decision_mode")

    return (len(reasons) == 0, reasons)