from typing import Any


def render_memory_content(content: dict[str, Any]) -> str:
    if not isinstance(content, dict) or not content:
        return ""

    parts = []
    for key, value in content.items():
        parts.append(f"{key}: {value}")
    return "; ".join(parts)
