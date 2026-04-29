from typing import Dict, Any

from memory.service import get_memories


def build_profile(subject_type: str, subject_id: str) -> Dict[str, Any]:
    items = get_memories(
        subject_type=subject_type,
        subject_id=subject_id,
        limit=100,
    )

    profile: Dict[str, Any] = {
        "subject_type": subject_type,
        "subject_id": subject_id,
        "facts": {},
        "preferences": {},
        "all_active": [],
    }

    for item in items:
        content = item.get("content") or {}
        memory_kind = item.get("memory_kind")

        if isinstance(content, dict):
            for key, value in content.items():
                profile["all_active"].append({key: value})

                if memory_kind == "preference":
                    profile["preferences"][key] = value
                else:
                    profile["facts"][key] = value

    return profile
