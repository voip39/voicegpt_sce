from __future__ import annotations

from runtime.outcome import OutcomeObject
from runtime.renderers.policies import VOICE_POLICY_REGISTRY
from runtime.renderers.result import RenderResult
from runtime.renderers.delivery_context import build_delivery_context


def render_voice_outcome(outcome: OutcomeObject) -> RenderResult:
    base_text = (outcome.speech_text or outcome.text or "").strip()
    template_family = outcome.template_family or ""

    ctx = build_delivery_context(outcome)
    keep_open = ctx.get("keep_open", True)
    farewell = (ctx.get("farewell") or "").strip()

    entry = VOICE_POLICY_REGISTRY.get(template_family)
    if entry:
        fn, policy_family_name = entry
        rendered = (fn(base_text) or "").strip()
        variant = "policy_text"
        policy_family = policy_family_name
        policy_applied = True
    else:
        rendered = base_text
        variant = "speech_text"
        policy_family = "default"
        policy_applied = False

    # 🔥 Phase 15B — VERY soft close (only if needed)
    if not keep_open and farewell:
        # не вставляем длинный farewell
        # делаем мягкое завершение
        if not rendered.endswith("."):
            rendered = f"{rendered}."

        rendered = f"{rendered} Let me know if you need anything else."

    return RenderResult(
        text=rendered,
        renderer="voice",
        variant_used=variant,
        policy_family=policy_family,
        policy_applied=policy_applied,
    )