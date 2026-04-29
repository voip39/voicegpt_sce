from __future__ import annotations

from runtime.outcome import OutcomeObject
from runtime.renderers.result import RenderResult
from runtime.renderers.delivery_context import build_delivery_context


def render_telegram_outcome(outcome: OutcomeObject) -> RenderResult:
    base_text = (outcome.short_text or outcome.text or "").strip()

    ctx = build_delivery_context(outcome)
    keep_open = ctx.get("keep_open", True)

    rendered = base_text

    # Phase 15E — compact close semantics for Telegram
    if not keep_open:
        if not rendered.endswith("."):
            rendered = f"{rendered}."

        if not rendered.endswith("Let me know if you need anything else."):
            rendered = f"{rendered} Let me know if you need anything else."

    return RenderResult(
        text=rendered,
        renderer="telegram",
        variant_used="short_text" if (outcome.short_text or "").strip() else "text",
        policy_family="default",
        policy_applied=False,
    )