from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
import uuid
from datetime import datetime, timezone


class MemoryItem(BaseModel):
    memory_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject_type: str
    subject_id: str
    memory_kind: str
    content: Dict[str, Any]
    source: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MemoryWriteRequest(BaseModel):
    subject_type: str
    subject_id: str
    memory_kind: str
    content: Dict[str, Any]
    source: Optional[str] = None


class MemoryReadQuery(BaseModel):
    subject_type: str
    subject_id: str
    memory_kind: Optional[str] = None
    limit: int = 10
