from typing import Any, Dict, List, Optional


def resolve_name(profile: Dict[str, Any], memory_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    name_profile = _profile_name(profile)
    name_memory = _extract(memory_items, "name")

    if name_profile:
        return _result(
            value=name_profile,
            selected_path="name_recall_profile",
            profile_used=True,
            memory_used=False,
            history_used=False,
        )

    if name_memory:
        return _result(
            value=name_memory,
            selected_path="name_recall_memory",
            profile_used=False,
            memory_used=True,
            history_used=False,
        )

    return _empty("name_recall_empty")


def resolve_favorite_color(profile: Dict[str, Any], memory_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    color_profile = _profile_favorite_color(profile)
    color_memory = _extract(memory_items, "favorite_color")

    if color_profile:
        return _result(
            value=color_profile,
            selected_path="favorite_color_recall_profile",
            profile_used=True,
            memory_used=False,
            history_used=False,
        )

    if color_memory:
        return _result(
            value=color_memory,
            selected_path="favorite_color_recall_memory",
            profile_used=False,
            memory_used=True,
            history_used=False,
        )

    return _empty("favorite_color_recall_empty")


def resolve_favorite_food(profile: Dict[str, Any], memory_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    food_profile = _profile_favorite_food(profile)
    food_memory = _extract(memory_items, "favorite_food")

    if food_profile:
        return _result(
            value=food_profile,
            selected_path="favorite_food_recall_profile",
            profile_used=True,
            memory_used=False,
            history_used=False,
        )

    if food_memory:
        return _result(
            value=food_memory,
            selected_path="favorite_food_recall_memory",
            profile_used=False,
            memory_used=True,
            history_used=False,
        )

    return _empty("favorite_food_recall_empty")


def resolve_previous_message(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not history:
        return _empty("previous_message_recall_empty")

    for item in reversed(history):
        if not isinstance(item, dict):
            continue
        if item.get("role") == "user" and item.get("text"):
            return _result(
                value=item["text"],
                selected_path="previous_message_recall_history",
                profile_used=False,
                memory_used=False,
                history_used=True,
            )

    return _empty("previous_message_recall_empty")


def resolve_history_summary(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not history:
        return _empty("conversation_summary_empty")

    texts: List[str] = []
    for item in history:
        if not isinstance(item, dict):
            continue
        if item.get("role") == "user" and item.get("text"):
            texts.append(str(item["text"]).strip())

    texts = [t for t in texts if t]

    if not texts:
        return _empty("conversation_summary_empty")

    summary = "; ".join(texts[-3:])

    return _result(
        value=summary,
        selected_path="conversation_summary_history",
        profile_used=False,
        memory_used=False,
        history_used=True,
    )


def resolve_profile_summary(profile: Dict[str, Any], memory_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary_from_profile = _profile_summary(profile)
    if summary_from_profile:
        return _result(
            value=summary_from_profile,
            selected_path="profile_summary_profile",
            profile_used=True,
            memory_used=False,
            history_used=False,
        )

    summary_from_memory = _memory_profile_summary(memory_items)
    if summary_from_memory:
        return _result(
            value=summary_from_memory,
            selected_path="profile_summary_memory",
            profile_used=False,
            memory_used=True,
            history_used=False,
        )

    return _empty("profile_summary_empty")


# =========================
# Helpers
# =========================

def _result(
    *,
    value: Any,
    selected_path: str,
    profile_used: bool,
    memory_used: bool,
    history_used: bool,
) -> Dict[str, Any]:
    return {
        "found": True,
        "value": value,
        "selected_path": selected_path,
        "profile_used": profile_used,
        "memory_used": memory_used,
        "history_used": history_used,
    }


def _empty(selected_path: str) -> Dict[str, Any]:
    return {
        "found": False,
        "value": None,
        "selected_path": selected_path,
        "profile_used": False,
        "memory_used": False,
        "history_used": False,
    }


def _extract(memory_items: List[Dict[str, Any]], key: str) -> Optional[Any]:
    for item in memory_items:
        if not isinstance(item, dict):
            continue
        content = item.get("content") or {}
        if isinstance(content, dict) and key in content and content[key] not in (None, "", [], {}):
            return content[key]
    return None


def _profile_name(profile: Dict[str, Any]) -> Optional[str]:
    identity = profile.get("identity") or {}
    value = identity.get("name")
    return str(value).strip() if value else None


def _profile_favorite_color(profile: Dict[str, Any]) -> Optional[str]:
    preferences = profile.get("preferences") or {}
    value = preferences.get("favorite_color")
    return str(value).strip() if value else None


def _profile_favorite_food(profile: Dict[str, Any]) -> Optional[str]:
    preferences = profile.get("preferences") or {}
    value = preferences.get("favorite_food")
    return str(value).strip() if value else None


def _profile_summary(profile: Dict[str, Any]) -> Optional[str]:
    parts: List[str] = []

    name = _profile_name(profile)
    color = _profile_favorite_color(profile)
    food = _profile_favorite_food(profile)

    if name:
        parts.append(f"name: {name}")
    if color:
        parts.append(f"favorite color: {color}")
    if food:
        parts.append(f"favorite food: {food}")

    if not parts:
        return None

    return "; ".join(parts)


def _memory_profile_summary(memory_items: List[Dict[str, Any]]) -> Optional[str]:
    latest: Dict[str, Any] = {}

    for item in memory_items:
        if not isinstance(item, dict):
            continue
        content = item.get("content") or {}
        if not isinstance(content, dict):
            continue

        if "name" in content and "name" not in latest and content["name"] not in (None, "", [], {}):
            latest["name"] = content["name"]

        if "favorite_color" in content and "favorite_color" not in latest and content["favorite_color"] not in (None, "", [], {}):
            latest["favorite_color"] = content["favorite_color"]

        if "favorite_food" in content and "favorite_food" not in latest and content["favorite_food"] not in (None, "", [], {}):
            latest["favorite_food"] = content["favorite_food"]

    parts: List[str] = []

    if "name" in latest:
        parts.append(f"name: {latest['name']}")
    if "favorite_color" in latest:
        parts.append(f"favorite color: {latest['favorite_color']}")
    if "favorite_food" in latest:
        parts.append(f"favorite food: {latest['favorite_food']}")

    if not parts:
        return None

    return "; ".join(parts)