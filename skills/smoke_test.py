import asyncio

from skills.loader import load_all_skills
from skills.registry import registry
from skills.executor import SkillExecutor
from skills.contracts import SkillInvocation


async def main():
    load_all_skills()

    print("registered skills:", registry.list_skills())

    executor = SkillExecutor()

    invocation = SkillInvocation(
        skill_name="kb_search",
        args={"query": "phase 4 smoke test"},
        tenant_id=1,
        session_id="smoke-session",
        thread_id="smoke-thread",
        requested_by="smoke-test",
    )

    result = await executor.execute(invocation)

    print("result:")
    print(result.model_dump())


if __name__ == "__main__":
    asyncio.run(main())
