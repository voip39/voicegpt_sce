from __future__ import annotations

import re
from typing import Any, Mapping

from agent.answer_synthesis import synthesize_memory_answer
from agent.recommendation import build_recommendation_from_memory
from agent.executor import execute_plan
from memory.semantic_retrieval import semantic_memory_search
from memory.hybrid_retrieval import hybrid_memory_search
from memory.ranking import rank_memory_candidates


EXACT_PATTERNS = [
    re.compile(r"\bwhat is my\b", re.IGNORECASE),
    re.compile(r"\bwhat's my\b", re.IGNORECASE),
    re.compile(r"\bwhich is my\b", re.IGNORECASE),
    re.compile(r"\btell me my\b", re.IGNORECASE),
]

PROFILE_PATTERNS = [
    re.compile(r"\bwhat do you know about me\b", re.IGNORECASE),
    re.compile(r"\bwhat do you remember about me\b", re.IGNORECASE),
    re.compile(r"\bprofile summary\b", re.IGNORECASE),
    re.compile(r"\bsummarize what you know about me\b", re.IGNORECASE),
]

BROAD_PATTERNS = [
    re.compile(r"\bwhat do i like\b", re.IGNORECASE),
    re.compile(r"\bwhat do i love\b", re.IGNORECASE),
    re.compile(r"\bwhat are my preferences\b", re.IGNORECASE),
    re.compile(r"\bwhat do you know i like\b", re.IGNORECASE),
]

PREFERENCE_HINT_PATTERNS = [
    re.compile(r"\bfavorite\b", re.IGNORECASE),
    re.compile(r"\bprefer\b", re.IGNORECASE),
    re.compile(r"\blike\b", re.IGNORECASE),
    re.compile(r"\blove\b", re.IGNORECASE),
]


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_dict(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    return {}


def _safe_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    return []


def _extract_user_text(payload: Mapping[str, Any]) -> str:
    last_event = _safe_dict(payload.get("last_event"))
    content = _safe_dict(last_event.get("content"))
    return _safe_text(content.get("text"))


def _matches_any(text: str, patterns: list[re.Pattern]) -> bool:
    return any(p.search(text) for p in patterns)


def _extract_pairs_from_content(content: Any) -> list[tuple[str, str]]:
    content = _safe_dict(content)
    pairs: list[tuple[str, str]] = []

    for key, value in content.items():
        k = _safe_text(key)
        v = _safe_text(value)
        if k and v:
            pairs.append((k, v))

    return pairs


def classify_query_mode(user_text: str, memory_result: Mapping[str, Any] | None = None) -> str:
    text = _safe_text(user_text)

    if not text:
        return "semantic_fact"

    if _matches_any(text, PROFILE_PATTERNS):
        return "profile_summary"

    if _matches_any(text, BROAD_PATTERNS):
        return "broad_summary"

    if _matches_any(text, EXACT_PATTERNS):
        key = ""
        if memory_result:
            key = _safe_text(memory_result.get("key"))

        lowered_key = key.lower()

        if lowered_key and (
            lowered_key.startswith("favorite_")
            or lowered_key.startswith("favorite ")
            or "prefer" in lowered_key
            or "like" in lowered_key
        ):
            return "preference_fact"

        if _matches_any(text, PREFERENCE_HINT_PATTERNS):
            return "preference_fact"

        return "exact_fact"

    if _matches_any(text, PREFERENCE_HINT_PATTERNS):
        return "preference_fact"

    return "semantic_fact"


def _extract_key_value(memory_result: Mapping[str, Any]) -> tuple[str, str]:
    key = _safe_text(memory_result.get("key"))
    value = _safe_text(memory_result.get("value"))

    if key and value:
        return key, value

    item = _safe_dict(memory_result.get("item"))
    key = _safe_text(item.get("key"))
    value = _safe_text(item.get("value"))
    if key and value:
        return key, value

    memory = _safe_dict(memory_result.get("memory"))
    key = _safe_text(memory.get("key"))
    value = _safe_text(memory.get("value"))
    if key and value:
        return key, value

    content = _safe_dict(memory_result.get("content"))
    pairs = _extract_pairs_from_content(content)
    if pairs:
        return pairs[0]

    items = _safe_list(memory_result.get("items"))
    for row in items:
        if isinstance(row, dict):
            row_key = _safe_text(row.get("key"))
            row_value = _safe_text(row.get("value"))
            if row_key and row_value:
                return row_key, row_value

            content = _safe_dict(row.get("content"))
            pairs = _extract_pairs_from_content(content)
            if pairs:
                return pairs[0]

    return "", ""


def _extract_items(memory_result: Mapping[str, Any]) -> list[tuple[str, str]]:
    raw_items = (
        _safe_list(memory_result.get("items"))
        or _safe_list(memory_result.get("results"))
        or _safe_list(memory_result.get("matches"))
    )

    output: list[tuple[str, str]] = []

    for row in raw_items:
        if isinstance(row, dict):
            key = _safe_text(row.get("key"))
            value = _safe_text(row.get("value"))
            if key and value:
                output.append((key, value))
                continue

            content = _safe_dict(row.get("content"))
            pairs = _extract_pairs_from_content(content)
            output.extend(pairs)

        elif isinstance(row, (list, tuple)) and len(row) >= 2:
            key = _safe_text(row[0])
            value = _safe_text(row[1])
            if key and value:
                output.append((key, value))

    if not output:
        content = _safe_dict(memory_result.get("content"))
        pairs = _extract_pairs_from_content(content)
        output.extend(pairs)

    return output


def _extract_profile_sections(memory_result: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    facts = _safe_dict(memory_result.get("facts"))
    preferences = _safe_dict(memory_result.get("preferences"))
    recent = _safe_dict(memory_result.get("recent"))

    if facts or preferences or recent:
        return facts, preferences, recent

    profile = _safe_dict(memory_result.get("profile"))
    facts = _safe_dict(profile.get("facts"))
    preferences = _safe_dict(profile.get("preferences"))
    recent = _safe_dict(profile.get("recent"))

    return facts, preferences, recent


def _empty_memory_response(user_text: str) -> str:
    text = _safe_text(user_text).lower()

    if "what do i like" in text or "preferences" in text:
        return "I do not have enough memory yet to tell what you like."

    if "what do you know about me" in text or "remember about me" in text:
        return "I do not know much about you yet."

    return "I could not find a clear answer in memory."


def build_memory_answer(
    user_text: str,
    memory_result: Mapping[str, Any] | None,
) -> dict[str, Any]:
    memory_result = memory_result or {}
    query_mode = classify_query_mode(user_text, memory_result)

    if query_mode in {"exact_fact", "preference_fact", "semantic_fact"}:
        key, value = _extract_key_value(memory_result)
        if not key or not value:
            return {
                "ok": False,
                "query_mode": query_mode,
                "text": _empty_memory_response(user_text),
            }

        text = synthesize_memory_answer(
            query_mode=query_mode,
            key=key,
            value=value,
        )
        return {
            "ok": True,
            "query_mode": query_mode,
            "text": text,
            "memory_key": key,
            "memory_value": value,
        }

    if query_mode == "broad_summary":
        items = _extract_items(memory_result)

        if not items:
            facts, preferences, recent = _extract_profile_sections(memory_result)
            if facts or preferences or recent:
                text = synthesize_memory_answer(
                    query_mode="profile_summary",
                    facts=facts,
                    preferences=preferences,
                    recent=recent,
                )
                return {
                    "ok": True,
                    "query_mode": "profile_summary",
                    "text": text,
                }

            return {
                "ok": False,
                "query_mode": query_mode,
                "text": _empty_memory_response(user_text),
            }

        text = synthesize_memory_answer(
            query_mode="broad_summary",
            items=items,
        )
        return {
            "ok": True,
            "query_mode": query_mode,
            "text": text,
            "items_used": items,
        }

    if query_mode == "profile_summary":
        facts, preferences, recent = _extract_profile_sections(memory_result)

        if not facts and not preferences and not recent:
            return {
                "ok": False,
                "query_mode": query_mode,
                "text": _empty_memory_response(user_text),
            }

        text = synthesize_memory_answer(
            query_mode="profile_summary",
            facts=facts,
            preferences=preferences,
            recent=recent,
        )
        return {
            "ok": True,
            "query_mode": query_mode,
            "text": text,
            "facts": facts,
            "preferences": preferences,
            "recent": recent,
        }

    return {
        "ok": False,
        "query_mode": query_mode,
        "text": "I could not synthesize a clear answer from memory.",
    }


def decide_l2_response(
    payload: Mapping[str, Any],
    memory_result: Mapping[str, Any] | None = None,
    default_response: str | None = None,
) -> dict[str, Any]:
    user_text = _extract_user_text(payload)

    if memory_result:
        memory_answer = build_memory_answer(user_text=user_text, memory_result=memory_result)
        return {
            "decision": "memory_answer",
            "query_mode": memory_answer.get("query_mode"),
            "response_text": memory_answer.get("text"),
            "memory_ok": memory_answer.get("ok", False),
            "memory_details": memory_answer,
        }

    return {
        "decision": "default_answer",
        "query_mode": None,
        "response_text": default_response or "I am ready to help.",
        "memory_ok": False,
        "memory_details": None,
    }


def decide_from_user_text(
    user_text: str,
    memory_result: Mapping[str, Any] | None = None,
    default_response: str | None = None,
) -> dict[str, Any]:
    payload = {
        "last_event": {
            "content": {
                "text": user_text
            }
        }
    }
    return decide_l2_response(
        payload=payload,
        memory_result=memory_result,
        default_response=default_response,
    )


def _profile_to_sections(profile: Mapping[str, Any] | None) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    profile = _safe_dict(profile)

    facts = _safe_dict(profile.get("facts"))
    preferences = _safe_dict(profile.get("preferences"))

    recent = {}
    all_active = profile.get("all_active")
    if isinstance(all_active, list):
        for item in all_active[:5]:
            if isinstance(item, dict):
                for key, value in item.items():
                    k = _safe_text(key)
                    v = _safe_text(value)
                    if k and v and k not in facts and k not in preferences:
                        recent[k] = v

    return facts, preferences, recent


def _normalize_hybrid_result(items: list[dict]) -> dict[str, Any]:
    if not items:
        return {}

    result_items = []

    for row in items:
        if not isinstance(row, dict):
            continue

        content = _safe_dict(row.get("content"))
        pairs = _extract_pairs_from_content(content)

        if pairs:
            for key, value in pairs:
                result_items.append({
                    "key": key,
                    "value": value,
                    "content": content,
                })
            continue

        key = _safe_text(row.get("key"))
        value = _safe_text(row.get("value"))
        if key and value:
            result_items.append({
                "key": key,
                "value": value,
            })

    result: dict[str, Any] = {"items": result_items}

    if result_items:
        result["key"] = result_items[0]["key"]
        result["value"] = result_items[0]["value"]

    return result


def _normalize_semantic_result(items: list[dict]) -> dict[str, Any]:
    if not items:
        return {}

    result_items = []

    for row in items:
        if not isinstance(row, dict):
            continue

        content = _safe_dict(row.get("content"))
        pairs = _extract_pairs_from_content(content)

        if pairs:
            for key, value in pairs:
                result_items.append({
                    "key": key,
                    "value": value,
                    "content": content,
                })
            continue

        key = _safe_text(row.get("key"))
        value = _safe_text(row.get("value"))
        if key and value:
            result_items.append({
                "key": key,
                "value": value,
            })

    result: dict[str, Any] = {}

    if result_items:
        result["key"] = result_items[0]["key"]
        result["value"] = result_items[0]["value"]
        result["items"] = result_items

    return result


def _build_ranking_preview(items: list[dict], limit: int = 5) -> list[dict[str, Any]]:
    preview = []

    for row in items[:limit]:
        if not isinstance(row, dict):
            continue

        content = _safe_dict(row.get("content"))
        key = ""
        value = ""

        pairs = _extract_pairs_from_content(content)
        if pairs:
            key, value = pairs[0]
        else:
            key = _safe_text(row.get("key"))
            value = _safe_text(row.get("value"))

        preview.append({
            "key": key,
            "value": value,
            "memory_kind": _safe_text(row.get("memory_kind")),
            "score": row.get("score"),
            "ranking_score": row.get("ranking_score"),
        })

    return preview


def _response_text(text: str) -> dict[str, Any]:
    return {
        "type": "text",
        "text": text,
    }


def collect_evidence(context: Mapping[str, Any], understanding: Mapping[str, Any], strategy: Mapping[str, Any]) -> dict[str, Any]:
    context = _safe_dict(context)
    understanding = _safe_dict(understanding)
    strategy = _safe_dict(strategy)

    state = _safe_dict(context.get("state"))
    profile = _safe_dict(context.get("profile"))

    last_event = _safe_dict(understanding.get("last_event") or state.get("last_event"))
    user_text = _extract_user_text({"last_event": last_event})

    evidence = {
        "profile": profile,
        "retrieved_items": [],
        "ranked_items": [],
        "memory_result": None,
        "ranking_trace": None,
    }

    mode = strategy.get("mode")

    # === BROAD MEMORY ===
    if mode == "memory_broad":
        items = hybrid_memory_search(
            subject_type=_safe_text(state.get("subject_type")),
            subject_id=_safe_text(state.get("subject_id")),
            query_text=user_text,
            key=None,
            memory_kind=None,
            limit=10,
        )

        ranked_items = rank_memory_candidates(items or [], limit=10)

        memory_result = _normalize_hybrid_result(ranked_items or [])
        memory_result = {"items": memory_result.get("items", [])}

        evidence.update({
            "retrieved_items": items or [],
            "ranked_items": ranked_items or [],
            "memory_result": memory_result,
            "ranking_trace": {
                "query_mode": "broad_summary",
                "retrieved_count": len(items or []),
                "ranked_count": len(ranked_items or []),
                "retrieved_preview": _build_ranking_preview(items or []),
                "ranked_preview": _build_ranking_preview(ranked_items or []),
            }
        })

        return evidence

    # === MEMORY RECOMMENDATION ===
    if mode == "memory_recommendation":
        recommendation_query = "what do I like"

        items = hybrid_memory_search(
            subject_type=_safe_text(state.get("subject_type")),
            subject_id=_safe_text(state.get("subject_id")),
            query_text=recommendation_query,
            key=None,
            memory_kind=None,
            limit=10,
        )

        ranked_items = rank_memory_candidates(items or [], limit=10)

        memory_result = _normalize_hybrid_result(ranked_items or [])
        memory_result = {"items": memory_result.get("items", [])}

        evidence.update({
            "retrieved_items": items or [],
            "ranked_items": ranked_items or [],
            "memory_result": memory_result,
            "ranking_trace": {
                "query_mode": "memory_recommendation",
                "retrieved_count": len(items or []),
                "ranked_count": len(ranked_items or []),
                "retrieved_preview": _build_ranking_preview(items or []),
                "ranked_preview": _build_ranking_preview(ranked_items or []),
            }
        })

        return evidence

    # === MEMORY RECOMMENDATION MOVIES ===
    if mode == "memory_recommendation_movies":
        recommendation_query = "what do I like"

        items = hybrid_memory_search(
            subject_type=_safe_text(state.get("subject_type")),
            subject_id=_safe_text(state.get("subject_id")),
            query_text=recommendation_query,
            key=None,
            memory_kind=None,
            limit=10,
        )

        ranked_items = rank_memory_candidates(items or [], limit=10)

        memory_result = _normalize_hybrid_result(ranked_items or [])
        memory_result = {"items": memory_result.get("items", [])}

        evidence.update({
            "retrieved_items": items or [],
            "ranked_items": ranked_items or [],
            "memory_result": memory_result,
            "ranking_trace": {
                "query_mode": "memory_recommendation_movies",
                "retrieved_count": len(items or []),
                "ranked_count": len(ranked_items or []),
                "retrieved_preview": _build_ranking_preview(items or []),
                "ranked_preview": _build_ranking_preview(ranked_items or []),
            }
        })

        return evidence

    # === MEMORY RECOMMENDATION BOOKS ===
    if mode == "memory_recommendation_books":
        recommendation_query = "what do I like"

        items = hybrid_memory_search(
            subject_type=_safe_text(state.get("subject_type")),
            subject_id=_safe_text(state.get("subject_id")),
            query_text=recommendation_query,
            key=None,
            memory_kind=None,
            limit=10,
        )

        ranked_items = rank_memory_candidates(items or [], limit=10)

        memory_result = _normalize_hybrid_result(ranked_items or [])
        memory_result = {"items": memory_result.get("items", [])}

        evidence.update({
            "retrieved_items": items or [],
            "ranked_items": ranked_items or [],
            "memory_result": memory_result,
            "ranking_trace": {
                "query_mode": "memory_recommendation_books",
                "retrieved_count": len(items or []),
                "ranked_count": len(ranked_items or []),
                "retrieved_preview": _build_ranking_preview(items or []),
                "ranked_preview": _build_ranking_preview(ranked_items or []),
            }
        })

        return evidence

    # === EXACT MEMORY ===
    if mode == "memory_exact":
        memory_query = _safe_dict(understanding.get("memory_query"))
        key = _safe_text(memory_query.get("key"))

        items = hybrid_memory_search(
            subject_type=_safe_text(state.get("subject_type")),
            subject_id=_safe_text(state.get("subject_id")),
            query_text=user_text or key,
            key=key or None,
            memory_kind=None,
            limit=5,
        )

        memory_result = _normalize_hybrid_result(items or [])

        evidence.update({
            "retrieved_items": items or [],
            "memory_result": memory_result,
        })

        return evidence

    # === PROFILE SUMMARY ===
    if mode == "memory_profile":
        evidence.update({
            "profile": profile,
        })
        return evidence

    return evidence


def select_strategy(context: Mapping[str, Any], understanding: Mapping[str, Any]) -> dict[str, Any]:
    understanding = _safe_dict(understanding)
    intent = _safe_text(understanding.get("intent")) or "message_received"

    strategy = {
        "intent_family": "chat",
        "mode": "chat_default",
        "needs_memory": False,
        "needs_search": False,
        "needs_skill": False,
        "needs_ranking": False,
        "needs_synthesis": False,
    }

    if intent == "memory_summary":
        strategy.update({
            "intent_family": "memory",
            "mode": "memory_profile",
            "needs_memory": True,
            "needs_synthesis": True,
        })
        return strategy

    if intent == "memory_recall":
        strategy.update({
            "intent_family": "memory",
            "mode": "memory_exact",
            "needs_memory": True,
            "needs_synthesis": True,
        })
        return strategy

    if intent == "memory_recommendation_movies":
        strategy.update({
            "intent_family": "memory",
            "mode": "memory_recommendation_movies",
            "needs_memory": True,
            "needs_ranking": True,
            "needs_synthesis": True,
        })
        return strategy

    if intent == "memory_recommendation_books":
        strategy.update({
            "intent_family": "memory",
            "mode": "memory_recommendation_books",
            "needs_memory": True,
            "needs_ranking": True,
            "needs_synthesis": True,
        })
        return strategy

    if intent == "memory_recommendation":
        strategy.update({
            "intent_family": "memory",
            "mode": "memory_recommendation",
            "needs_memory": True,
            "needs_ranking": True,
            "needs_synthesis": True,
        })
        return strategy

    if intent == "memory_semantic_recall":
        memory_query = _safe_dict(understanding.get("memory_query"))
        query_text = _safe_text(memory_query.get("query_text")).lower().strip()

        if query_text in {"what do i like", "what things do i like"}:
            strategy.update({
                "intent_family": "memory",
                "mode": "memory_broad",
                "needs_memory": True,
                "needs_ranking": True,
                "needs_synthesis": True,
            })
        else:
            strategy.update({
                "intent_family": "memory",
                "mode": "memory_semantic",
                "needs_memory": True,
                "needs_synthesis": True,
            })
        return strategy

    if intent == "kb_search":
        strategy.update({
            "intent_family": "skill",
            "mode": "skill_kb_search",
            "needs_skill": True,
        })
        return strategy

    if intent == "send_sms":
        strategy.update({
            "intent_family": "skill",
            "mode": "skill_send_sms",
            "needs_skill": True,
        })
        return strategy

    if intent == "handoff_request":
        strategy.update({
            "intent_family": "skill",
            "mode": "skill_handoff",
            "needs_skill": True,
        })
        return strategy

    if intent == "memory_store":
        strategy.update({
            "intent_family": "skill",
            "mode": "skill_memory_write",
            "needs_skill": True,
        })
        return strategy

    return strategy


def build_plan(strategy: Mapping[str, Any]) -> dict[str, Any]:
    strategy = _safe_dict(strategy)
    mode = _safe_text(strategy.get("mode"))

    steps = []

    if mode == "memory_profile":
        steps = ["load_profile", "summarize_profile"]

    elif mode == "memory_exact":
        steps = ["retrieve_memory", "select_fact", "synthesize_answer"]

    elif mode == "memory_broad":
        steps = ["retrieve_memory", "rank_candidates", "build_shortlist", "synthesize_answer"]

    elif mode == "memory_semantic":
        steps = ["semantic_retrieve", "select_candidate", "synthesize_answer"]

    elif mode == "memory_recommendation":
        steps = ["retrieve_memory", "rank_candidates", "build_shortlist", "infer_preferences", "recommend_generic"]

    elif mode == "memory_recommendation_books":
        steps = ["retrieve_memory", "rank_candidates", "build_shortlist", "infer_preferences", "recommend_books"]

    elif mode == "memory_recommendation_movies":
        steps = ["retrieve_memory", "rank_candidates", "build_shortlist", "infer_preferences", "recommend_movies"]

    elif mode == "skill_kb_search":
        steps = ["prepare_skill_request", "run_kb_search", "format_result"]

    elif mode == "skill_send_sms":
        steps = ["prepare_skill_request", "run_send_sms", "format_result"]

    elif mode == "skill_handoff":
        steps = ["prepare_skill_request", "run_handoff", "format_result"]

    elif mode == "skill_memory_write":
        steps = ["prepare_skill_request", "write_memory", "format_result"]

    else:
        steps = ["respond_default"]

    return {
        "mode": mode or "unknown",
        "steps": steps,
    }


def decide(context: Mapping[str, Any], understanding: Mapping[str, Any]) -> dict[str, Any]:
    context = _safe_dict(context)
    understanding = _safe_dict(understanding)

    state = _safe_dict(context.get("state"))
    profile = _safe_dict(context.get("profile"))
    intent = _safe_text(understanding.get("intent")) or "message_received"
    strategy = select_strategy(context, understanding)
    plan = build_plan(strategy)
    evidence = collect_evidence(context, understanding, strategy)

    last_event = _safe_dict(understanding.get("last_event") or state.get("last_event"))
    user_text = _extract_user_text({"last_event": last_event})

    base = {
        "action": "respond",
        "response": _response_text("I am ready to help."),
        "intent": intent,
        "strategy": strategy,
        "plan": plan,
    }

    if intent == "kb_search":
        query = _safe_text(understanding.get("query"))
        return {
            "action": "call_skill",
            "intent": intent,
            "strategy": strategy,
            "plan": plan,
            "skill_request": {
                "skill_name": "kb_search",
                "arguments": {
                    "query": query,
                },
            },
        }

    if intent == "send_sms":
        sms_text = _safe_text(understanding.get("sms_text"))
        return {
            "action": "call_skill",
            "intent": intent,
            "strategy": strategy,
            "plan": plan,
            "skill_request": {
                "skill_name": "send_sms",
                "arguments": {
                    "text": sms_text,
                },
            },
        }

    if intent == "handoff_request":
        handoff_reason = _safe_text(understanding.get("handoff_reason"))
        return {
            "action": "call_skill",
            "intent": intent,
            "strategy": strategy,
            "plan": plan,
            "skill_request": {
                "skill_name": "handoff_request",
                "arguments": {
                    "reason": handoff_reason,
                },
            },
        }

    if intent == "memory_store":
        memory_payload = _safe_text(understanding.get("memory_payload"))
        return {
            "action": "call_skill",
            "intent": intent,
            "strategy": strategy,
            "plan": plan,
            "skill_request": {
                "skill_name": "memory_write",
                "arguments": {
                    "subject_type": _safe_text(state.get("subject_type")),
                    "subject_id": _safe_text(state.get("subject_id")),
                    "text": memory_payload,
                },
            },
        }

    if intent == "memory_summary":
        facts, preferences, recent = _profile_to_sections(profile)
        text = synthesize_memory_answer(
            query_mode="profile_summary",
            facts=facts,
            preferences=preferences,
            recent=recent,
        )
        return {
            "action": "respond",
            "intent": intent,
            "strategy": strategy,
            "plan": plan,
            "response": _response_text(text),
        }

    if intent == "memory_recommendation_movies":
        from agent.recommendation import build_movie_recommendation_from_memory

        memory_result = _safe_dict(evidence.get("memory_result"))
        items = memory_result.get("items", []) or []

        text = build_movie_recommendation_from_memory(items)

        execution = execute_plan(
            plan=plan,
            intent=intent,
            strategy=strategy,
            evidence=evidence,
            response_text=text,
        )

        result = {
            "action": "respond",
            "intent": intent,
            "strategy": strategy,
            "plan": plan,
            "response": _response_text(execution["response_text"]),
            "memory": {"items_used": items},
            "execution_trace": execution["execution_trace"],
        }

        ranking_trace = evidence.get("ranking_trace")
        if ranking_trace:
            result["ranking_trace"] = ranking_trace

        return result

    if intent == "memory_recommendation_books":
        from agent.recommendation import build_book_recommendation_from_memory

        memory_result = _safe_dict(evidence.get("memory_result"))
        items = memory_result.get("items", []) or []

        text = build_book_recommendation_from_memory(items)

        execution = execute_plan(
            plan=plan,
            intent=intent,
            strategy=strategy,
            evidence=evidence,
            response_text=text,
        )

        result = {
            "action": "respond",
            "intent": intent,
            "strategy": strategy,
            "plan": plan,
            "response": _response_text(execution["response_text"]),
            "memory": {"items_used": items},
            "execution_trace": execution["execution_trace"],
        }

        ranking_trace = evidence.get("ranking_trace")
        if ranking_trace:
            result["ranking_trace"] = ranking_trace

        return result

    if intent == "memory_recommendation":
        memory_result = _safe_dict(evidence.get("memory_result"))
        items = memory_result.get("items", []) or []
        recommendation_text = build_recommendation_from_memory(items)

        execution = execute_plan(
            plan=plan,
            intent=intent,
            strategy=strategy,
            evidence=evidence,
            response_text=recommendation_text,
        )

        result = {
            "action": "respond",
            "intent": intent,
            "strategy": strategy,
            "plan": plan,
            "response": _response_text(execution["response_text"]),
            "memory": {
                "items_used": items,
            },
            "execution_trace": execution["execution_trace"],
        }

        ranking_trace = evidence.get("ranking_trace")
        if ranking_trace is not None:
            result["ranking_trace"] = ranking_trace

        return result

    if intent == "memory_recall":
        memory_query = _safe_dict(understanding.get("memory_query"))
        key = _safe_text(memory_query.get("key"))

        items = hybrid_memory_search(
            subject_type=_safe_text(state.get("subject_type")),
            subject_id=_safe_text(state.get("subject_id")),
            query_text=user_text or key,
            key=key or None,
            memory_kind=None,
            limit=5,
        )
        memory_result = _normalize_hybrid_result(items or [])

        l2 = decide_l2_response(
            payload={"last_event": last_event},
            memory_result=memory_result,
            default_response="I could not find a clear answer in memory.",
        )

        return {
            "action": "respond",
            "intent": intent,
            "strategy": strategy,
            "plan": plan,
            "response": _response_text(l2["response_text"]),
            "memory": l2.get("memory_details"),
        }

    if intent == "memory_semantic_recall":
        memory_query = _safe_dict(understanding.get("memory_query"))
        query_text = _safe_text(memory_query.get("query_text")) or user_text
        lowered_user_text = user_text.lower().strip()

        ranking_trace = None

        if lowered_user_text in {"what do i like", "what things do i like"}:
            items = hybrid_memory_search(
                subject_type=_safe_text(state.get("subject_type")),
                subject_id=_safe_text(state.get("subject_id")),
                query_text=query_text,
                key=None,
                memory_kind=None,
                limit=10,
            )
            ranked_items = rank_memory_candidates(items or [], limit=10)
            memory_result = _normalize_hybrid_result(ranked_items or [])
            memory_result = {"items": memory_result.get("items", [])}

            ranking_trace = {
                "query_mode": "broad_summary",
                "retrieved_count": len(items or []),
                "ranked_count": len(ranked_items or []),
                "retrieved_preview": _build_ranking_preview(items or []),
                "ranked_preview": _build_ranking_preview(ranked_items or []),
            }
        else:
            items = semantic_memory_search(
                subject_type=_safe_text(state.get("subject_type")),
                subject_id=_safe_text(state.get("subject_id")),
                query_text=query_text,
                limit=5,
            )
            memory_result = _normalize_semantic_result(items or [])

        l2 = decide_l2_response(
            payload={"last_event": last_event},
            memory_result=memory_result,
            default_response="I could not find anything relevant in memory.",
        )

        result = {
            "action": "respond",
            "intent": intent,
            "strategy": strategy,
            "plan": plan,
            "response": _response_text(l2["response_text"]),
            "memory": l2.get("memory_details"),
        }

        if ranking_trace is not None:
            result["ranking_trace"] = ranking_trace

        return result

    if intent == "message_received":
        return {
            "action": "respond",
            "intent": intent,
            "strategy": strategy,
            "plan": plan,
            "response": _response_text("I am ready to help."),
        }

    return base
