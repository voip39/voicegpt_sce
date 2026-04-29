from fastapi import FastAPI, HTTPException
from typing import Dict, Any

from core.validator import validate_event
from runtime.agent_runtime import handle_turn
from channels.web.router import router as web_router
from channels.telegram.router import router as telegram_router

app = FastAPI(title="VoiceGPT SCE API", version="0.3")

app.include_router(web_router, prefix="/channels/web")
app.include_router(telegram_router, prefix="/channels/telegram")


@app.post("/sce/event")
async def sce_event(event: Dict[str, Any]):
    try:
        validated = validate_event(event)
        result = handle_turn(validated.model_dump())

        return {
            "ok": True,
            "result": result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))