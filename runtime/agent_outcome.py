from __future__ import annotations

from typing import Any, Dict, List, Optional


def build_agent_outcome(
    *,
    agent_type: str,
    reply: str,
    decision_type: str = "answer",
    profile_used: bool = False,
    memory_used: bool = False,
    execution_trace: Optional[Dict[str, Any]] = None,
    observations: Optional[List[Any]] = None,
    state_patch: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "ok": True,
        "agent_type": agent_type,
        "decision_type": decision_type,
        "reply": reply,
        "profile_used": profile_used,
        "memory_used": memory_used,
        "execution_trace": execution_trace or {},
        "observations": observations or [],
        "state_patch": state_patch or {},
    }