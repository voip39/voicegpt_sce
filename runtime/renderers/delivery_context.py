from __future__ import annotations

from typing import Any, Dict


def build_delivery_context(outcome) -> Dict[str, Any]:
    hints = outcome.channel_hints or {}

    return {
        "language": hints.get("language") or "en",
        "persona": hints.get("persona"),
        "keep_open": hints.get("keep_open", True),
        "farewell": hints.get("farewell"),
        "greeting": hints.get("greeting"),
    }