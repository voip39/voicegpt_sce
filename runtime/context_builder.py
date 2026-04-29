from __future__ import annotations

from typing import Any, Dict, List, Optional

from runtime.profile_builder import build_user_profile


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _normalize_memory_items(
    recall_result: Optional[Dict[str, Any]] = None,
    memory_items: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    if isinstance(memory_items, list):
        return [x for x in memory_items if isinstance(x, dict)]

    if isinstance(recall_result, dict):
        items = recall_result.get("items", [])
        if isinstance(items, list):
            return [x for x in items if isinstance(x, dict)]

    return []


def build_runtime_context(
    *,
    current_turn: Optional[Dict[str, Any]] = None,
    continuity_ctx: Optional[Dict[str, Any]] = None,
    recall_result: Optional[Dict[str, Any]] = None,
    tenant_ctx: Optional[Dict[str, Any]] = None,
    memory_items: Optional[List[Dict[str, Any]]] = None,
    state: Optional[Dict[str, Any]] = None,
    event: Optional[Dict[str, Any]] = None,
    tenant_profile: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Phase 8.9B

    Canonical runtime context builder with backward-compatible aliases.

    Main target shape:
    runtime_ctx = {
        "current_turn": {...},
        "continuity": {...},
        "memory": {
            "items": [...],
            "count": N,
        },
        "profile": {...},
        "tenant": {...},
    }
    """

    current_turn = _safe_dict(current_turn) or _safe_dict(event)
    continuity_ctx = _safe_dict(continuity_ctx) or _safe_dict(state)
    tenant_ctx = _safe_dict(tenant_ctx) or _safe_dict(tenant_profile)

    normalized_memory_items = _normalize_memory_items(
        recall_result=recall_result,
        memory_items=memory_items,
    )

    user_profile = build_user_profile(normalized_memory_items)

    runtime_ctx = {
        "current_turn": current_turn,
        "continuity": continuity_ctx,
        "memory": {
            "items": normalized_memory_items,
            "count": len(normalized_memory_items),
        },
        "profile": user_profile,
        "tenant": tenant_ctx,
    }

    return runtime_ctx


def build_context(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """
    Backward-compatible wrapper for older runtime code.

    Supported patterns:
    1) build_context(current_turn=..., continuity_ctx=..., recall_result=..., tenant_ctx=...)
    2) build_context(event=..., state=..., recall_result=..., tenant_profile=...)
    3) build_context(current_turn, continuity_ctx, recall_result, tenant_ctx)
    4) build_context(event, state)
    """

    if kwargs:
        return build_runtime_context(**kwargs)

    if len(args) == 4:
        return build_runtime_context(
            current_turn=_safe_dict(args[0]),
            continuity_ctx=_safe_dict(args[1]),
            recall_result=_safe_dict(args[2]),
            tenant_ctx=_safe_dict(args[3]),
        )

    if len(args) == 3:
        return build_runtime_context(
            current_turn=_safe_dict(args[0]),
            continuity_ctx=_safe_dict(args[1]),
            recall_result=_safe_dict(args[2]),
        )

    if len(args) == 2:
        return build_runtime_context(
            event=_safe_dict(args[0]),
            state=_safe_dict(args[1]),
        )

    if len(args) == 1:
        return build_runtime_context(
            current_turn=_safe_dict(args[0]),
        )

    return build_runtime_context()


def debug_runtime_context(runtime_ctx: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "has_current_turn": bool(runtime_ctx.get("current_turn")),
        "has_continuity": bool(runtime_ctx.get("continuity")),
        "memory_count": runtime_ctx.get("memory", {}).get("count", 0),
        "has_profile": bool(runtime_ctx.get("profile")),
        "has_tenant": bool(runtime_ctx.get("tenant")),
    }