from typing import List, Dict, Any
from core.db import db_all


def _normalize_query(query: str) -> str:
    return (query or "").strip().lower()


def _query_targets_name(query: str) -> bool:
    q = _normalize_query(query)
    triggers = {
        "what is my name",
        "what's my name",
        "who am i",
        "my name",
        "name",
    }
    return q in triggers or " my name" in q or q == "name"


def _query_targets_favorite_color(query: str) -> bool:
    q = _normalize_query(query)
    return "favorite color" in q or "favourite color" in q or q == "color" or q == "colour"


def _query_targets_favorite_food(query: str) -> bool:
    q = _normalize_query(query)
    return "favorite food" in q or "favourite food" in q or q == "food"


def _is_profile_query(query: str) -> bool:
    q = _normalize_query(query)
    return q in {
        "what do you know about me",
        "tell me about me",
        "what do you remember about me",
    }


def _is_relevant_memory(query: str, item: Dict[str, Any]) -> bool:
    content = item.get("content") or {}
    if not isinstance(content, dict):
        return False

    if _query_targets_name(query) and "name" in content:
        return True

    if _query_targets_favorite_color(query) and "favorite_color" in content:
        return True

    if _query_targets_favorite_food(query) and "favorite_food" in content:
        return True

    if _is_profile_query(query):
        return True

    return False


def recall_memory(tenant_id: int, subject_id: str, query: str) -> List[Dict[str, Any]]:
    try:
        rows = db_all(
            """
            SELECT memory_kind, content, source, created_at
            FROM runtime.memory_items
            WHERE subject_type = 'user'
              AND subject_id = %s
              AND status = 'active'
            ORDER BY created_at DESC
            LIMIT 25
            """,
            (subject_id,),
        )
    except Exception:
        return []

    raw_items: List[Dict[str, Any]] = []

    for r in rows:
        raw_items.append(
            {
                "kind": r.get("memory_kind"),
                "content": r.get("content") or {},
                "source": r.get("source"),
                "created_at": r.get("created_at"),
            }
        )

    relevant = [item for item in raw_items if _is_relevant_memory(query, item)]
    if relevant:
        return relevant[:10]

    return raw_items[:5]