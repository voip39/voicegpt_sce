from __future__ import annotations

from runtime.outcome import OutcomeObject
from runtime.renderers.result import RenderResult
from runtime.renderers.delivery_context import build_delivery_context

WEB_GREETING_DEFAULT = ""


def render_web_outcome(outcome: OutcomeObject) -> RenderResult:
    body = (outcome.text or "").strip()

    ctx = build_delivery_context(outcome)

    greeting = (ctx.get("greeting") or WEB_GREETING_DEFAULT).strip()
    farewell = (ctx.get("farewell") or "").strip()
    keep_open = ctx.get("keep_open", True)

    if greeting and body:
        if not body.startswith(greeting):
            rendered = f"{greeting} {body}".strip()
        else:
            rendered = body
    elif greeting:
        rendered = greeting
    else:
        rendered = body

    if not keep_open and farewell:
        if not rendered.endswith(farewell):
            rendered = f"{rendered} {farewell}".strip()

    return RenderResult(
        text=rendered,
        renderer="web",
        variant_used="text",
        policy_family="default",
        policy_applied=False,
    )