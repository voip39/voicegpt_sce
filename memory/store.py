import json
import uuid
from typing import Any

from runtime.db import get_conn
from memory.vector_store import index_memory_item


_ALLOWED_MEMORY_KINDS = {
    "user_fact",
    "preference",
    "session_fact",
    "derived_fact",
}


def _validate_memory_kind(memory_kind: str) -> None:
    if memory_kind not in _ALLOWED_MEMORY_KINDS:
        raise ValueError(
            f"Unsupported memory_kind='{memory_kind}'. "
            f"Allowed: {sorted(_ALLOWED_MEMORY_KINDS)}"
        )


def _extract_single_kv(content: dict[str, Any]) -> tuple[str, Any]:
    if not isinstance(content, dict) or not content:
        raise ValueError("memory content must be a non-empty dict")

    if len(content) != 1:
        raise ValueError("baseline memory_write supports exactly one key/value pair")

    key = next(iter(content.keys()))
    value = content[key]
    return str(key), value


def write_memory(
    subject_type: str,
    subject_id: str,
    memory_kind: str,
    content: dict[str, Any],
    source: str,
) -> dict[str, Any]:
    _validate_memory_kind(memory_kind)

    key, value = _extract_single_kv(content)
    memory_id = str(uuid.uuid4())

    importance = 0.5
    confidence = 0.8

    if memory_kind == "preference":
        importance = 0.7
        confidence = 0.9
    elif memory_kind == "derived_fact":
        importance = 0.4
        confidence = 0.6
    elif memory_kind == "session_fact":
        importance = 0.3
        confidence = 0.7

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, content
                FROM runtime.memory_items
                WHERE subject_type = %s
                  AND subject_id = %s
                  AND status = 'active'
                ORDER BY created_at DESC
                """,
                (subject_type, subject_id),
            )
            active_rows = cur.fetchall()

            existing_same_key_id = None
            existing_same_key_value = None

            for row in active_rows:
                row_id = row[0]
                row_content = row[1] or {}

                if isinstance(row_content, dict) and key in row_content:
                    existing_same_key_id = row_id
                    existing_same_key_value = row_content.get(key)
                    break

            if existing_same_key_id is not None and existing_same_key_value == value:
                return {"status": "deduplicated"}

            if existing_same_key_id is not None and existing_same_key_value != value:
                cur.execute(
                    """
                    UPDATE runtime.memory_items
                    SET status = 'superseded',
                        updated_at = now()
                    WHERE id = %s
                    """,
                    (existing_same_key_id,),
                )

            cur.execute(
                """
                INSERT INTO runtime.memory_items
                (memory_id, subject_type, subject_id, memory_kind, content, source, status,
                 importance, confidence, updated_at)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s, 'active', %s, %s, now())
                RETURNING id, subject_type, subject_id, content, importance, confidence
                """,
                (
                    memory_id,
                    subject_type,
                    subject_id,
                    memory_kind,
                    json.dumps(content),
                    source,
                    importance,
                    confidence,
                ),
            )
            row = cur.fetchone()
            conn.commit()

    embedding_row = index_memory_item(
        memory_item_id=row[0],
        subject_type=row[1],
        subject_id=row[2],
        content=row[3],
    )

    return {
        "status": "accepted",
        "memory": {
            "id": row[0],
            "content": row[3],
            "importance": row[4],
            "confidence": row[5],
        },
        "embedding": embedding_row,
    }
