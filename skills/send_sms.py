from skills.contracts import SkillDefinition, SkillInvocation, SideEffectLevel
from skills.registry import registry


class SendSMSSkill:
    async def execute(self, invocation: SkillInvocation):
        to = invocation.args.get("to", "").strip()
        text = invocation.args.get("text", "").strip()

        if not to:
            return {
                "status": "rejected",
                "reason": "missing 'to'"
            }

        if not text:
            return {
                "status": "rejected",
                "reason": "missing 'text'"
            }

        return {
            "status": "accepted",
            "provider": "stub",
            "to": to,
            "text": text
        }


definition = SkillDefinition(
    skill_name="send_sms",
    description="Send SMS message",
    side_effect_level=SideEffectLevel.HIGH,
    allowed_agent_classes=None,
    allowed_agent_roles=None,
    channel_support=["sms", "voice", "web"],
)

registry.register(definition, SendSMSSkill())
