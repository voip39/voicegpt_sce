from memory.retrieval import read_memory
from memory.service import MemoryQuery
from memory.profile import build_profile


def build_context(state) -> dict:
    memory_query = MemoryQuery(
        subject_type=state.subject_type,
        subject_id=state.subject_id,
        limit=10,
    )

    memory_items = read_memory(
        subject_type=memory_query.subject_type,
        subject_id=memory_query.subject_id,
        key=memory_query.key,
        memory_kind=memory_query.memory_kind,
        limit=memory_query.limit,
    )

    profile = build_profile(
        subject_type=state.subject_type,
        subject_id=state.subject_id,
    )

    return {
        "state": state.model_dump(),
        "memory": memory_items,
        "profile": profile,
    }
