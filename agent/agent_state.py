from pydantic import BaseModel, Field
from typing import Dict, Any


class AgentState(BaseModel):
    thread_id: str
    session_id: str
    subject_type: str
    subject_id: str

    tenant_id: int | None = None
    tenant_kind: str | None = None

    last_event_id: str | None = None
    last_event: Dict[str, Any] | None = None

    counters: Dict[str, Any] = Field(default_factory=dict)
