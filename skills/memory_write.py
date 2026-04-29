from memory.store import write_memory
from skills.contracts import SkillDefinition, SkillInvocation, SkillResult
from skills.registry import registry


def _validate_args(args: dict) -> dict:
    subject_type = args.get("subject_type")
    subject_id = args.get("subject_id")
    memory_kind = args.get("memory_kind")
    content = args.get("content")
    source = args.get("source", "skill:memory_write")

    if not subject_type:
        raise ValueError("memory_write requires subject_type")

    if not subject_id:
        raise ValueError("memory_write requires subject_id")

    if not memory_kind:
        raise ValueError("memory_write requires memory_kind")

    if not isinstance(content, dict) or not content:
        raise ValueError("memory_write requires non-empty dict content")

    return {
        "subject_type": subject_type,
        "subject_id": subject_id,
        "memory_kind": memory_kind,
        "content": content,
        "source": source,
    }


async def handler(invocation: SkillInvocation) -> SkillResult:
    try:
        item = _validate_args(invocation.args)

        row = write_memory(
            subject_type=item["subject_type"],
            subject_id=item["subject_id"],
            memory_kind=item["memory_kind"],
            content=item["content"],
            source=item["source"],
        )

        return SkillResult(
            skill_name=invocation.skill_name,
            invocation_id=invocation.invocation_id,
            status="success",
            result={
                "status": "accepted",
                "memory": row,
            },
            error_code=None,
            error_message=None,
            latency_ms=0,
            side_effect_committed=True,
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
    skill_name="memory_write",
    description="Write a user memory item and supersede older matching items.",
    input_schema={
        "type": "object",
        "properties": {
            "subject_type": {"type": "string"},
            "subject_id": {"type": "string"},
            "memory_kind": {"type": "string"},
            "content": {"type": "object"},
            "source": {"type": "string"},
        },
        "required": ["subject_type", "subject_id", "memory_kind", "content"],
        "additionalProperties": True,
    },
)

registry.register(definition, handler)