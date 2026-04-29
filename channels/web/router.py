from fastapi import APIRouter, Request, HTTPException
import uuid
from datetime import datetime, timezone

from core.validator import validate_event
from runtime.agent_runtime import handle_turn

router = APIRouter()


@router.post("/inbound")
async def web_inbound(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    tenant_id = data.get("tenant_id")
    if tenant_id is None:
        raise HTTPException(status_code=400, detail="Missing tenant_id")

    text = data.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Missing text")

    session_id = data.get("session_id") or str(uuid.uuid4())
    thread_id = data.get("thread_id") or session_id

    identity = data.get("identity") or {}
    subject_id = identity.get("id") or f"web:anon:{uuid.uuid4()}"

    tenant_kind = data.get("tenant_kind") or "unknown"
    now_iso = datetime.now(timezone.utc).isoformat()

    sce_event = {
        "sce_version": "2.0",
        "event": {
            "id": str(uuid.uuid4()),
            "kind": "message",
            "action": "received",
            "direction": "inbound",
            "ts": now_iso,
        },
        "subject": {
            "type": "user",
            "subject_id": subject_id,
        },
        "content": {
            "modality": "text",
            "text": text,
        },
        "route": {
            "tenant_id": int(tenant_id),
            "channel": "web",
            "channel_family": "chat",
            "session_id": session_id,
        },
        "context": {
            "tenant_id": int(tenant_id),
            "tenant_kind": tenant_kind,
            "thread_id": thread_id,
            "session_id": session_id,
        },
        "meta": {
            "source": "web_adapter",
            "schema_version": "2.0",
        },
    }

    try:
        validated = validate_event(sce_event)
        payload = validated.model_dump()
        result = handle_turn(payload)

        return {
            "ok": True,
            "result": result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))