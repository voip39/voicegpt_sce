from core.sce_v2 import SCEEnvelope
from pydantic import ValidationError


def validate_event(data: dict) -> SCEEnvelope:
    try:
        return SCEEnvelope.model_validate(data)
    except ValidationError as e:
        raise ValueError(e.errors())
