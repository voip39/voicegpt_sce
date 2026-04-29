from runtime.db import get_connection


def get_subject_events(subject_type: str, subject_id: str) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT payload_json
                FROM runtime.events
                WHERE subject_type = %s
                  AND subject_id = %s
                ORDER BY id ASC
                """,
                (subject_type, subject_id),
            )
            rows = cur.fetchall()

    return [row[0] for row in rows]


def build_subject_projection(subject_type: str, subject_id: str) -> dict:
    events = get_subject_events(subject_type, subject_id)

    return {
        "subject": {
            "type": subject_type,
            "subject_id": subject_id,
        },
        "event_count": len(events),
        "events": events,
    }
