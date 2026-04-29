from typing import Optional, List, Dict, Any, Union

from pydantic import BaseModel

from memory.retrieval import read_memory


class MemoryQuery(BaseModel):
    subject_type: str
    subject_id: str
    key: Optional[str] = None
    memory_kind: Optional[str] = None
    limit: int = 10


def get_memory(query_obj: MemoryQuery) -> List[Dict[str, Any]]:
    result = read_memory(
        subject_type=query_obj.subject_type,
        subject_id=query_obj.subject_id,
        key=query_obj.key,
        memory_kind=query_obj.memory_kind,
        limit=query_obj.limit,
    )
    if not isinstance(result, list):
        return []
    return result


def get_memories(
    subject_type: Union[str, MemoryQuery],
    subject_id: Optional[str] = None,
    key: Optional[str] = None,
    memory_kind: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    if isinstance(subject_type, MemoryQuery):
        return get_memory(subject_type)

    if subject_id is None:
        raise ValueError("get_memories requires subject_id when called without MemoryQuery")

    result = read_memory(
        subject_type=subject_type,
        subject_id=subject_id,
        key=key,
        memory_kind=memory_kind,
        limit=limit,
    )
    if not isinstance(result, list):
        return []
    return result


def get_memory_value(
    subject_type: Union[str, MemoryQuery],
    subject_id: Optional[str] = None,
    key: Optional[str] = None,
    memory_kind: Optional[str] = None,
    limit: int = 10,
    default: Any = None,
) -> Any:
    if isinstance(subject_type, MemoryQuery):
        query_obj = subject_type
        items = get_memory(query_obj)
        key = query_obj.key
    else:
        if subject_id is None:
            raise ValueError("get_memory_value requires subject_id when called without MemoryQuery")

        items = get_memories(
            subject_type=subject_type,
            subject_id=subject_id,
            key=key,
            memory_kind=memory_kind,
            limit=limit,
        )

    if not items:
        return default

    if key:
        for item in items:
            content = item.get("content") or {}
            if isinstance(content, dict) and key in content:
                return content.get(key)
        return default

    first = items[0]
    content = first.get("content") or {}
    if isinstance(content, dict) and len(content) == 1:
        return next(iter(content.values()))

    return content if content else default
