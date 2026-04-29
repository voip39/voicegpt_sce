from typing import Dict, Any
from datetime import datetime
import json

from core.db import db_one, db_exec

MAX_HISTORY = 6


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _key(tenant_id: int, thread_id: str, subject_id: str) -> str:
    return f"{tenant_id}:{thread_id}:{subject_id}"


# -------- NEW: фильтр служебных сообщений --------
def _is_meta_message(text: str) -> bool:
    if not text:
        return False

    t = text.strip().lower()

    triggers = {
        "what did i say before",
        "what did i say previously",
        "what was my previous message",
        "what was my last message",
        "what did i just say",
        "what did we talk about",
        "summarize conversation",
        "what have we discussed",
        "give me summary",
    }

    return t in triggers


def init_state(
    tenant_id: int,
    thread_id: str,
    session_id: str,
    subject_id: str,
    agent_type: str,
) -> Dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "thread_id": thread_id,
        "session_id": session_id,
        "subject_id": subject_id,
        "agent_type": agent_type,

        "active_goal": None,
        "current_intent": None,
        "slots": {},
        "pending_action": None,

        "history": [],
        "last_user_message": None,
        "last_agent_reply": None,

        "updated_at": _now_iso(),
    }


def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    if not row:
        return row

    history = row.get("history")
    if isinstance(history, str):
        try:
            history = json.loads(history)
        except Exception:
            history = []
    if history is None:
        history = []

    slots = row.get("slots")
    if isinstance(slots, str):
        try:
            slots = json.loads(slots)
        except Exception:
            slots = {}
    if slots is None:
        slots = {}

    return {
        "tenant_id": row["tenant_id"],
        "thread_id": row["thread_id"],
        "session_id": row["session_id"],
        "subject_id": row["subject_id"],
        "agent_type": row["agent_type"],

        "active_goal": row.get("active_goal"),
        "current_intent": row.get("current_intent"),
        "slots": slots,
        "pending_action": row.get("pending_action"),

        "history": history,
        "last_user_message": row.get("last_user_message"),
        "last_agent_reply": row.get("last_agent_reply"),

        "updated_at": str(row.get("updated_at")) if row.get("updated_at") else _now_iso(),
    }


def load_state(
    tenant_id: int,
    thread_id: str,
    session_id: str,
    subject_id: str,
    agent_type: str,
) -> Dict[str, Any]:
    row = db_one(
        """
        SELECT *
        FROM runtime.agent_continuity
        WHERE tenant_id = %s
          AND thread_id = %s
          AND subject_id = %s
        """,
        (tenant_id, thread_id, subject_id),
    )

    if row:
        return _normalize_row(row)

    state = init_state(tenant_id, thread_id, session_id, subject_id, agent_type)
    save_state(state)
    return state


def append_history(state: Dict[str, Any], role: str, text: str) -> None:
    if not text:
        return

    # -------- фильтрация --------
    if role == "user" and _is_meta_message(text):
        return

    history = state.get("history") or []

    history.append({
        "role": role,
        "text": text,
    })

    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    state["history"] = history


def save_state(state: Dict[str, Any]) -> None:
    db_exec(
        """
        INSERT INTO runtime.agent_continuity (
            tenant_id,
            thread_id,
            session_id,
            subject_id,
            agent_type,
            active_goal,
            current_intent,
            slots,
            pending_action,
            history,
            last_user_message,
            last_agent_reply,
            updated_at
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s::jsonb, %s,
            %s::jsonb, %s, %s, NOW()
        )
        ON CONFLICT (tenant_id, thread_id, subject_id)
        DO UPDATE SET
            session_id = EXCLUDED.session_id,
            agent_type = EXCLUDED.agent_type,
            active_goal = EXCLUDED.active_goal,
            current_intent = EXCLUDED.current_intent,
            slots = EXCLUDED.slots,
            pending_action = EXCLUDED.pending_action,
            history = EXCLUDED.history,
            last_user_message = EXCLUDED.last_user_message,
            last_agent_reply = EXCLUDED.last_agent_reply,
            updated_at = NOW()
        """,
        (
            state["tenant_id"],
            state["thread_id"],
            state["session_id"],
            state["subject_id"],
            state["agent_type"],
            state.get("active_goal"),
            state.get("current_intent"),
            json.dumps(state.get("slots") or {}),
            state.get("pending_action"),
            json.dumps(state.get("history") or []),
            state.get("last_user_message"),
            state.get("last_agent_reply"),
        ),
    )