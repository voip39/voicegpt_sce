from typing import Dict, List, Any
from skills.contracts import SkillDefinition


class SkillRegistry:
    def __init__(self):
        self._definitions: Dict[str, SkillDefinition] = {}
        self._implementations: Dict[str, Any] = {}

    def register(self, definition: SkillDefinition, implementation: Any) -> None:
        self._definitions[definition.skill_name] = definition
        self._implementations[definition.skill_name] = implementation

    def get_definition(self, skill_name: str) -> SkillDefinition | None:
        return self._definitions.get(skill_name)

    def get_implementation(self, skill_name: str) -> Any | None:
        return self._implementations.get(skill_name)

    def list_skills(self) -> List[str]:
        return list(self._definitions.keys())

    def has_skill(self, skill_name: str) -> bool:
        return skill_name in self._definitions


registry = SkillRegistry()

