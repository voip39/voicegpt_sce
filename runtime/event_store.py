import json
from runtime.db import get_connection


def save_event(event: dict):
    event_id = event.get("event", {}).get("id")
    thread_id = event.get("context", {}).get("thread_id")
    session_id = event.get("context", {}).get("session_id")
    subject_type = event.get("subject", {}).get("type")
    subject_id = event.get("subject", {}).get("subject_id")

    payload_json = json.dumps(event)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO runtime.events (
                    event_id,
                    thread_id,
                    session_id,
                    subject_type,
                    subject_id,
                    payload_json
                )
                VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    event_id,
                    thread_id,
                    session_id,
                    subject_type,
                    subject_id,
                    payload_json,
                ),
            )
        conn.commit()


def list_events() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT payload_json
                FROM runtime.events
                ORDER BY id ASC
                """
            )
            rows = cur.fetchall()

    return [row[0] for row in rows]


def clear_events():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM runtime.events")
        conn.commit()
