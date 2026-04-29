import re
from typing import Any, Dict


def parse_memory_write(text: str) -> Dict[str, Any]:
    t = _normalize(text)

    if not t:
        return _no_match()

    m = re.match(r"^my name is\s+(.+)$", t, flags=re.IGNORECASE)
    if m:
        value = _clean_value(m.group(1))
        if value:
            return {
                "matched": True,
                "memory_kind": "name",
                "value": value,
                "selected_path": "memory_write_name",
            }

    m = re.match(r"^call me\s+(.+)$", t, flags=re.IGNORECASE)
    if m:
        value = _clean_value(m.group(1))
        if value:
            return {
                "matched": True,
                "memory_kind": "name",
                "value": value,
                "selected_path": "memory_write_name",
            }

    m = re.match(r"^my favorite color is\s+(.+)$", t, flags=re.IGNORECASE)
    if m:
        value = _clean_value(m.group(1))
        if value:
            return {
                "matched": True,
                "memory_kind": "favorite_color",
                "value": value,
                "selected_path": "memory_write_favorite_color",
            }

    m = re.match(r"^my favourite colour is\s+(.+)$", t, flags=re.IGNORECASE)
    if m:
        value = _clean_value(m.group(1))
        if value:
            return {
                "matched": True,
                "memory_kind": "favorite_color",
                "value": value,
                "selected_path": "memory_write_favorite_color",
            }

    m = re.match(r"^my favorite food is\s+(.+)$", t, flags=re.IGNORECASE)
    if m:
        value = _clean_value(m.group(1))
        if value:
            return {
                "matched": True,
                "memory_kind": "favorite_food",
                "value": value,
                "selected_path": "memory_write_favorite_food",
            }

    if t.startswith("remember that "):
        payload = _clean_value(t[len("remember that "):])
        if payload:
            return {
                "matched": True,
                "memory_kind": "generic",
                "value": payload,
                "selected_path": "memory_write_generic",
            }

    if t.startswith("my ") or t.startswith("call me "):
        return {
            "matched": True,
            "memory_kind": "generic",
            "value": t,
            "selected_path": "memory_write_generic",
        }

    return _no_match()


def _normalize(text: str) -> str:
    return " ".join((text or "").strip().split())


def _clean_value(value: str) -> str:
    v = (value or "").strip().strip(".").strip()
    return v


def _no_match() -> Dict[str, Any]:
    return {
        "matched": False,
        "memory_kind": None,
        "value": None,
        "selected_path": "memory_write_unmatched",
    }