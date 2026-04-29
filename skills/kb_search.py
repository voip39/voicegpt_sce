from skills.contracts import SkillDefinition, SkillInvocation, SideEffectLevel
from skills.registry import registry


class KBSearchSkill:
    async def execute(self, invocation: SkillInvocation):
        query = invocation.args.get("query", "").strip()

        if not query:
            return {
                "matches": [],
                "count": 0,
                "note": "empty query"
            }

        return {
            "matches": [
                {
                    "id": "stub-1",
                    "title": "Stub KB Result",
                    "text": f"Result for query: {query}"
                }
            ],
            "count": 1
        }


definition = SkillDefinition(
    skill_name="kb_search",
    description="Search knowledge base",
    side_effect_level=SideEffectLevel.NONE,
    allowed_agent_classes=None,
    allowed_agent_roles=None,
    channel_support=None,
)

registry.register(definition, KBSearchSkill())
