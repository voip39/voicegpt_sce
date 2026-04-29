import time

from skills.registry import registry
from skills.contracts import SkillInvocation, SkillResult


class SkillExecutor:
    async def execute(self, invocation: SkillInvocation) -> SkillResult:
        start = time.time()

        definition = registry.get_definition(invocation.skill_name)
        implementation = registry.get_implementation(invocation.skill_name)

        if not definition or not implementation:
            return SkillResult(
                skill_name=invocation.skill_name,
                invocation_id=invocation.invocation_id,
                status="error",
                result=None,
                error_code="skill_not_found",
                error_message=f"Skill '{invocation.skill_name}' is not registered",
                latency_ms=int((time.time() - start) * 1000),
                side_effect_committed=False,
            )

        try:
            result = await implementation(invocation)

            if isinstance(result, SkillResult):
                result.latency_ms = int((time.time() - start) * 1000)
                return result

            return SkillResult(
                skill_name=invocation.skill_name,
                invocation_id=invocation.invocation_id,
                status="success",
                result=result,
                error_code=None,
                error_message=None,
                latency_ms=int((time.time() - start) * 1000),
                side_effect_committed=False,
            )

        except Exception as e:
            return SkillResult(
                skill_name=invocation.skill_name,
                invocation_id=invocation.invocation_id,
                status="error",
                result=None,
                error_code="execution_error",
                error_message=str(e),
                latency_ms=int((time.time() - start) * 1000),
                side_effect_committed=False,
            )