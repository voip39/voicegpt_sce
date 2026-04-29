from pydantic import BaseModel
from typing import Optional


class PolicyDecision(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    policy_code: Optional[str] = None
