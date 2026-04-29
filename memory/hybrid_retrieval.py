from typing import Any, Dict, List, Optional

from memory.retrieval import read_memory
from memory.semantic_retrieval import semantic_memory_search


def _detect_query_mode(query_text: str, key: Optional[str]) -> str:
    q = (query_text or "").strip().lower()

    if key:
        return "exact_fact"

    broad_markers = [
        "preferences",
        "preference",
        "taste",
        "tastes",
        "what do you know about me",
        "tell me about me",
        "what do i like",
        "likes",
    ]

    for marker in broad_markers:
        if marker in q:
            return "broad_summary"

    return "semantic_fact"


def _dedupe_candidates(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    result = []

    for item in items:
        memory_item_id = item.get("memory_item_id")
        if memory_item_id is None:
            memory_item_id = f"exact:{item.get('id')}"

        if memory_item_id in seen:
            continue

        seen.add(memory_item_id)
        result.append(item)

    return result


def _normalize_exact_items(items: List[Dict[str, Any]], score: float = 1.0) -> List[Dict[str, Any]]:
    normalized = []

    for item in items:
        normalized.append({
            "retrieval_mode": "exact",
            "memory_item_id": item.get("id"),
            "content": item.get("content"),
            "memory_kind": item.get("memory_kind"),
            "source": item.get("source"),
            "status": item.get("status"),
            "created_at": item.get("created_at"),
            "score": score,
        })

    return normalized


def _normalize_semantic_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []

    for item in items:
        normalized.append({
            "retrieval_mode": "semantic",
            "memory_item_id": item.get("memory_item_id"),
            "content": item.get("content"),
            "memory_kind": item.get("memory_kind"),
            "source": item.get("source"),
            "status": item.get("status"),
            "created_at": item.get("created_at"),
            "score": item.get("similarity", 0.0),
            "content_text": item.get("content_text"),
        })

    return normalized


def _broad_summary_candidates(
    subject_type: str,
    subject_id: str,
    query_text: str,
    limit: int,
) -> List[Dict[str, Any]]:
    preference_items = read_memory(
        subject_type=subject_type,
        subject_id=subject_id,
        memory_kind="preference",
        limit=limit,
    )

    general_items = read_memory(
        subject_type=subject_type,
        subject_id=subject_id,
        limit=limit,
    )

    semantic_items = semantic_memory_search(
        subject_type=subject_type,
        subject_id=subject_id,
        query_text=query_text,
        limit=limit,
    )

    merged = (
        _normalize_exact_items(preference_items, score=1.2)
        + _normalize_exact_items(general_items, score=0.95)
        + _normalize_semantic_items(semantic_items)
    )

    merged = _dedupe_candidates(merged)
    merged.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    return merged[:limit]


def hybrid_memory_search(
    subject_type: str,
    subject_id: str,
    query_text: str,
    key: Optional[str] = None,
    memory_kind: Optional[str] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    mode = _detect_query_mode(query_text, key)

    if mode == "broad_summary":
        return _broad_summary_candidates(
            subject_type=subject_type,
            subject_id=subject_id,
            query_text=query_text,
            limit=limit,
        )

    exact_items = []
    if key:
        exact_items = read_memory(
            subject_type=subject_type,
            subject_id=subject_id,
            key=key,
            memory_kind=memory_kind,
            limit=limit,
        )
    elif memory_kind:
        exact_items = read_memory(
            subject_type=subject_type,
            subject_id=subject_id,
            key=None,
            memory_kind=memory_kind,
            limit=limit,
        )

    semantic_items = semantic_memory_search(
        subject_type=subject_type,
        subject_id=subject_id,
        query_text=query_text,
        limit=limit,
    )

    merged = _normalize_exact_items(exact_items) + _normalize_semantic_items(semantic_items)
    merged = _dedupe_candidates(merged)
    merged.sort(key=lambda x: x.get("score", 0.0), reverse=True)

    return merged[:limit]
