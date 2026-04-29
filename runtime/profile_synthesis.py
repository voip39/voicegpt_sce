from typing import Any, Dict


def synthesize_profile_summary(resolver_result: Dict[str, Any]) -> str:
    """
    Принимает результат resolve_profile_summary(...)
    и возвращает cleaner human-readable summary text,
    уже готовый для вставки в reply.
    """
    if not resolver_result or not resolver_result.get("found"):
        return "I don’t have any stored information about you yet."

    raw_value = resolver_result.get("value")
    selected_path = resolver_result.get("selected_path") or ""

    if isinstance(raw_value, dict):
        return _synthesize_from_dict(raw_value, selected_path)

    if isinstance(raw_value, str):
        return _synthesize_from_flat_text(raw_value, selected_path)

    return "I don’t have any stored information about you yet."


def _synthesize_from_dict(data: Dict[str, Any], selected_path: str) -> str:
    name = _clean(data.get("name"))
    favorite_color = _clean(data.get("favorite_color"))
    favorite_food = _clean(data.get("favorite_food"))

    facts = []

    if name:
        facts.append(f"your name is {name}")
    if favorite_color:
        facts.append(f"your favorite color is {favorite_color}")
    if favorite_food:
        facts.append(f"your favorite food is {favorite_food}")

    if not facts:
        return "I don’t have any stored information about you yet."

    joined = _join_facts(facts)

    if selected_path == "profile_summary_memory":
        return f"Here’s what I know about you from memory: {joined}."
    return f"Here’s what I know about you: {joined}."


def _synthesize_from_flat_text(raw_text: str, selected_path: str) -> str:
    parsed = _parse_semicolon_kv(raw_text)

    if parsed:
        return _synthesize_from_dict(parsed, selected_path)

    cleaned = _clean(raw_text)
    if not cleaned:
        return "I don’t have any stored information about you yet."

    if selected_path == "profile_summary_memory":
        return f"Here’s what I know about you from memory: {cleaned}."
    return f"Here’s what I know about you: {cleaned}."


def _parse_semicolon_kv(raw_text: str) -> Dict[str, str]:
    """
    Парсит строки вида:
    'name: Victor; favorite color: blue; favorite food: sushi'
    """
    result: Dict[str, str] = {}

    parts = [p.strip() for p in (raw_text or "").split(";") if p.strip()]
    for part in parts:
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        key = key.strip().lower()
        value = _clean(value)

        if not value:
            continue

        if key == "name":
            result["name"] = value
        elif key in {"favorite color", "favourite colour"}:
            result["favorite_color"] = value
        elif key == "favorite food":
            result["favorite_food"] = value

    return result


def _join_facts(facts):
    if not facts:
        return ""
    if len(facts) == 1:
        return facts[0]
    if len(facts) == 2:
        return f"{facts[0]}, and {facts[1]}"
    return f"{', '.join(facts[:-1])}, and {facts[-1]}"


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().strip(".").strip()