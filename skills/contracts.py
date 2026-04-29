from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from enum import Enum
import time
import uuid


# --- Enums ---

class SkillStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


class SideEffectLevel(str, Enum):
    NONE = "none"
    LOW = "low"
    HIGH = "high"


# --- Skill Definition ---

class SkillDefinition(BaseModel):
    skill_name: str
    description: str

    side_effect_level: SideEffectLevel = SideEffectLevel.NONE

    allowed_agent_classes: Optional[List[str]] = None
    allowed_agent_roles: Optional[List[str]] = None
    channel_support: Optional[List[str]] = None


# --- Invocation ---

class SkillInvocation(BaseModel):
    skill_name: str

    invocation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    args: Dict[str, Any]

    tenant_id: Optional[int] = None
    session_id: Optional[str] = None
    thread_id: Optional[str] = None

    requested_by: Optional[str] = None

    created_at: float = Field(default_factory=lambda: time.time())


# --- Result ---

class SkillResult(BaseModel):
    skill_name: str
    invocation_id: str

    status: SkillStatus

    result: Optional[Dict[str, Any]] = None

    error_code: Optional[str] = None
    error_message: Optional[str] = None

    latency_ms: Optional[int] = None

    side_effect_committed: bool = False
