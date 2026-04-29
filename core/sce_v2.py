from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class Event(BaseModel):
    id: str
    kind: str
    action: str
    direction: str
    ts: str


class Subject(BaseModel):
    type: str
    subject_id: str


class Content(BaseModel):
    modality: str
    text: Optional[str] = None
    attachments: List[Any] = Field(default_factory=list)


class Route(BaseModel):
    tenant_id: int
    channel: str
    channel_family: str
    session_id: Optional[str] = None


class Context(BaseModel):
    tenant_id: int
    tenant_kind: str
    thread_id: str
    session_id: str


class Meta(BaseModel):
    schema_version: str
    source: Optional[str] = None
    extensions: Dict[str, Any] = Field(default_factory=dict)


class SCEEnvelope(BaseModel):
    sce_version: str = Field(default="2.0")

    event: Event
    subject: Subject
    content: Content
    route: Route
    context: Context
    meta: Meta