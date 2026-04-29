from __future__ import annotations

from runtime.outcome import OutcomeObject
from runtime.renderers.policies import SMS_POLICY_REGISTRY
from runtime.renderers.result import RenderResult
from runtime.renderers.delivery_context import build_delivery_context


def render_sms_outcome(outcome: OutcomeObject) -> RenderResult:
    base_text = (outcome.short_text or outcome.text or "").strip()
    template_family = outcome.template_family or ""

    ctx = build_delivery_context(outcome)
    keep_open = ctx.get("keep_open", True)

    entry = SMS_POLICY_REGISTRY.get(template_family)
    if entry:
        fn, policy_family_name = entry
        rendered = (fn(base_text) or "").strip()
        variant = "policy_text"
        policy_family = policy_family_name
        policy_applied = True
    else:
        rendered = base_text
        variant = "short_text"
        policy_family = "default"
        policy_applied = False

    # Phase 15C — compact close semantics for SMS
    if not keep_open:
        if not rendered.endswith("."):
            rendered = f"{rendered}."
        if not rendered.endswith(" Reply if needed."):
            rendered = f"{rendered} Reply if needed."

    return RenderResult(
        text=rendered,
        renderer="sms",
        variant_used=variant,
        policy_family=policy_family,
        policy_applied=policy_applied,
    )