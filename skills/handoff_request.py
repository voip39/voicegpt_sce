from skills.contracts import SkillDefinition, SkillInvocation, SideEffectLevel
from skills.registry import registry


class HandoffRequestSkill:
    async def execute(self, invocation: SkillInvocation):
        target = invocation.args.get("target", "").strip()
        reason = invocation.args.get("reason", "").strip()

        if not target:
            return {
                "status": "rejected",
                "reason": "missing 'target'"
            }

        return {
            "status": "accepted",
            "handoff_target": target,
            "reason": reason or "no reason provided"
        }


definition = SkillDefinition(
    skill_name="handoff_request",
    description="Request handoff to another executor or human",
    side_effect_level=SideEffectLevel.LOW,
    allowed_agent_classes=None,
    allowed_agent_roles=None,
    channel_support=["voice", "sms", "web"],
)

registry.register(definition, HandoffRequestSkill())
