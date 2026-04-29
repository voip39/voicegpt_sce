from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RenderResult:
    text: str
    renderer: str
    variant_used: str
    policy_family: Optional[str] = None
    policy_applied: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "renderer": self.renderer,
            "variant_used": self.variant_used,
            "policy_family": self.policy_family,
            "policy_applied": self.policy_applied,
        }