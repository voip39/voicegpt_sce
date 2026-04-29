from typing import List, Dict, Any
from datetime import datetime, timezone


def _safe_text(v):
    return str(v).strip() if v is not None else ""


def _parse_time(ts):
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def compute_score(item: Dict[str, Any]) -> float:
    score = 0.0

    # base retrieval score
    score += float(item.get("score", 0.0))

    # preference boost
    if item.get("memory_kind") == "preference":
        score += 1.5

    # favorite_* boost
    content = item.get("content", {}) or {}
    for key in content.keys():
        if key.startswith("favorite_"):
            score += 1.0

    # recency (простая версия, timezone-safe)
    created_at = item.get("created_at")
    dt = _parse_time(created_at)
    if dt:
        now = datetime.now(timezone.utc)
        age_days = max(0, (now - dt.astimezone(timezone.utc)).days)
        score += max(0, 1.0 - age_days * 0.05)

    return score


def rank_memory_candidates(items: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    scored = []

    for item in items:
        item_copy = dict(item)
        item_copy["ranking_score"] = compute_score(item_copy)
        scored.append(item_copy)

    scored.sort(key=lambda x: x.get("ranking_score", 0), reverse=True)

    # dedupe by key
    seen_keys = set()
    result = []

    for item in scored:
        content = item.get("content", {}) or {}

        for key, value in content.items():
            if key in seen_keys:
                continue

            seen_keys.add(key)
            result.append(item)
            break

        if len(result) >= limit:
            break

    return result
