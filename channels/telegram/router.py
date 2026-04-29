from fastapi import APIRouter, Request, HTTPException
import uuid
from datetime import datetime, timezone

from core.validator import validate_event
from runtime.agent_runtime import handle_turn
from channels.telegram.sender import send_telegram_message

router = APIRouter()


@router.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    print("TELEGRAM INCOMING UPDATE:", data)

    message = data.get("message") or {}
    text = message.get("text")

    if not text:
        print("TELEGRAM SKIP: no text in update")
        return {"ok": True}

    chat = message.get("chat") or {}
    chat_id = chat.get("id")

    user = message.get("from") or {}
    user_id = user.get("id")

    print("TELEGRAM PARSED chat_id:", chat_id)
    print("TELEGRAM PARSED user_id:", user_id)
    print("TELEGRAM PARSED text:", repr(text))

    if not chat_id or not user_id:
        print("TELEGRAM SKIP: missing chat_id or user_id")
        return {"ok": True}

    tenant_id = request.query_params.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Missing tenant_id")

    tenant_id = int(tenant_id)
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
            "subject_id": f"telegram:{user_id}",
        },
        "content": {
            "modality": "text",
            "text": text,
        },
        "route": {
            "tenant_id": tenant_id,
            "channel": "telegram",
            "channel_family": "chat",
            "session_id": f"telegram:{chat_id}",
        },
        "context": {
            "tenant_id": tenant_id,
            "tenant_kind": "unknown",
            "thread_id": f"telegram:{chat_id}",
            "session_id": f"telegram:{chat_id}",
        },
        "meta": {
            "source": "telegram_adapter",
            "schema_version": "2.0",
        },
    }

    print("TELEGRAM SCE EVENT:", sce_event)

    try:
        validated = validate_event(sce_event)
        payload = validated.model_dump()

        print("TELEGRAM VALIDATED PAYLOAD:", payload)

        result = handle_turn(payload)

        print("TELEGRAM RUNTIME RESULT:", result)

        reply_text = result.get("reply") or "OK"

        send_result = send_telegram_message(chat_id, reply_text)

        print("TELEGRAM SEND RESULT:", send_result)

        return {"ok": True}

    except Exception as e:
        print("TELEGRAM WEBHOOK EXCEPTION:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))