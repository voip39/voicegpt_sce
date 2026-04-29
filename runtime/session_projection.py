from runtime.db import get_connection


def get_session_events(session_id: str) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT payload_json
                FROM runtime.events
                WHERE session_id = %s
                ORDER BY id ASC
                """,
                (session_id,),
            )
            rows = cur.fetchall()

    return [row[0] for row in rows]


def build_session_projection(session_id: str) -> dict:
    events = get_session_events(session_id)

    return {
        "session_id": session_id,
        "event_count": len(events),
        "events": events,
    }
