from __future__ import annotations

from typing import Any, Dict, List, Optional


def _is_active_memory_item(item: Dict[str, Any]) -> bool:
    status = str(item.get("status") or "").strip().lower()
    return status in {"active", "current", ""}


def _extract_content_dict(item: Dict[str, Any]) -> Dict[str, Any]:
    content = item.get("content")
    if isinstance(content, dict):
        return content
    return {}


def _coerce_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return str(value).strip() or None


def empty_user_profile() -> Dict[str, Any]:
    return {
        "identity": {
            "name": None,
            "aliases": [],
        },
        "preferences": {
            "favorite_color": None,
            "favorite_food": None,
        },
        "facts": {},
        "behavior": {},
    }


def build_user_profile(memory_items: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    profile = empty_user_profile()

    if not memory_items:
        return profile

    for item in memory_items:
        if not isinstance(item, dict):
            continue

        if not _is_active_memory_item(item):
            continue

        content = _extract_content_dict(item)

        # identity
        if "name" in content:
            profile["identity"]["name"] = _coerce_str(content["name"])

        # preferences
        if "favorite_color" in content:
            profile["preferences"]["favorite_color"] = _coerce_str(content["favorite_color"])

        if "favorite_food" in content:
            profile["preferences"]["favorite_food"] = _coerce_str(content["favorite_food"])

    return profile


def summarize_user_profile(profile: Optional[Dict[str, Any]]) -> str:
    if not profile:
        return "I do not know much about you yet."

    identity = profile.get("identity", {})
    preferences = profile.get("preferences", {})

    parts = []

    if identity.get("name"):
        parts.append(f"name: {identity['name']}")

    if preferences.get("favorite_color"):
        parts.append(f"favorite color: {preferences['favorite_color']}")

    if preferences.get("favorite_food"):
        parts.append(f"favorite food: {preferences['favorite_food']}")

    if not parts:
        return "I do not know much about you yet."

    return "Here's what I know about you: " + "; ".join(parts) + "."