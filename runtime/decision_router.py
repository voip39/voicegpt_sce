from typing import Dict

from runtime.query_detectors import (
    is_empty,
    is_greeting,
    is_memory_write,
    is_profile_query,
    is_name_query,
    is_favorite_color_query,
    is_favorite_food_query,
    is_previous_message_query,
    is_history_query,
)


def route_decision(text: str) -> Dict[str, str]:
    """
    Phase 11.9 — routing-to-decision readiness

    Now returns richer structure:
    - route
    - family
    - matched_by
    - priority
    - capability
    - candidate_decision_type
    """

    if is_empty(text):
        return _r("empty", "system", "detector_empty", 0, "greeting", "greeting")

    if is_greeting(text):
        return _r("greeting", "system", "detector_greeting", 1, "greeting", "greeting")

    if is_profile_query(text):
        return _r("profile_query", "profile", "detector_profile_query", 3, "profile_summary", "profile_summary")

    if is_memory_write(text):
        return _r("memory_write", "write", "detector_memory_write", 4, "memory_write", "memory_write_ack")

    if is_name_query(text):
        return _r("name_recall", "memory", "detector_name_query", 5, "memory_recall", "memory_recall")

    if is_favorite_color_query(text):
        return _r("favorite_color_recall", "memory", "detector_favorite_color", 6, "memory_recall", "memory_recall")

    if is_favorite_food_query(text):
        return _r("favorite_food_recall", "memory", "detector_favorite_food", 7, "memory_recall", "memory_recall")

    if is_previous_message_query(text):
        return _r("previous_message", "continuity", "detector_previous_message", 8, "continuity_recall", "continuity_recall")

    if is_history_query(text):
        return _r("history_summary", "continuity", "detector_history_summary", 9, "conversation_summary", "conversation_summary")

    return _r("default_answer", "fallback", "detector_default", 10, "answer", "answer")


def _r(route: str, family: str, matched_by: str, priority: int, capability: str, decision_type: str) -> Dict[str, str]:
    return {
        "route": route,
        "family": family,
        "matched_by": matched_by,
        "priority": priority,
        "capability": capability,
        "candidate_decision_type": decision_type,
    }