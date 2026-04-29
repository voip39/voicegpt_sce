from runtime.db import get_connection


def get_thread_events(thread_id: str) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT payload_json
                FROM runtime.events
                WHERE thread_id = %s
                ORDER BY id ASC
                """,
                (thread_id,),
            )
            rows = cur.fetchall()

    return [row[0] for row in rows]


def build_thread_projection(thread_id: str) -> dict:
    events = get_thread_events(thread_id)

    return {
        "thread_id": thread_id,
        "event_count": len(events),
        "events": events,
    }
