from memory.retrieval import read_memory
from skills.contracts import SkillDefinition, SkillInvocation, SkillResult


def _validate_args(args: dict) -> dict:
    subject_type = args.get("subject_type")
    subject_id = args.get("subject_id")
    key = args.get("key")
    memory_kind = args.get("memory_kind")

    if not subject_type:
        raise ValueError("memory_read requires subject_type")

    if not subject_id:
        raise ValueError("memory_read requires subject_id")

    return {
        "subject_type": subject_type,
        "subject_id": subject_id,
        "key": key,
        "memory_kind": memory_kind,
    }


async def handler(invocation: SkillInvocation) -> SkillResult:
    try:
        args = _validate_args(invocation.args)

        items = read_memory(
            subject_type=args["subject_type"],
            subject_id=args["subject_id"],
            key=args["key"],
            memory_kind=args["memory_kind"],
        )

        return SkillResult(
            skill_name=invocation.skill_name,
            invocation_id=invocation.invocation_id,
            status="success",
            result={
                "count": len(items),
                "items": items,
            },
            error_code=None,
            error_message=None,
            latency_ms=0,
            side_effect_committed=False,
        )

    except Exception as exc:
        return SkillResult(
            skill_name=invocation.skill_name,
            invocation_id=invocation.invocation_id,
            status="error",
            result=None,
            error_code="execution_error",
            error_message=str(exc),
            latency_ms=0,
            side_effect_committed=False,
        )


definition = SkillDefinition(
    skill_name="memory_read",
    description="Read memory with optional filtering",
    input_schema={
        "type": "object",
        "properties": {
            "subject_type": {"type": "string"},
            "subject_id": {"type": "string"},
            "key": {"type": "string"},
            "memory_kind": {"type": "string"},
        },
        "required": ["subject_type", "subject_id"],
    },
)