from typing import Any, Optional, List, Dict

from runtime.db import get_conn


def _extract_key(content: dict) -> Optional[str]:
    if not isinstance(content, dict):
        return None
    if len(content) != 1:
        return None
    return next(iter(content.keys()))


def read_memory(
    subject_type: str,
    subject_id: str,
    key: Optional[str] = None,
    memory_kind: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT id, memory_id, subject_type, subject_id,
                       memory_kind, content, source, status, created_at
                FROM runtime.memory_items
                WHERE subject_type = %s
                  AND subject_id = %s
                  AND status = 'active'
            """
            params = [subject_type, subject_id]

            if memory_kind:
                query += " AND memory_kind = %s"
                params.append(memory_kind)

            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)

            cur.execute(query, params)
            rows = cur.fetchall()

    results = []

    for row in rows:
        content = row[5] or {}

        if key:
            k = _extract_key(content)
            if k != key:
                continue

        results.append({
            "id": row[0],
            "memory_id": row[1],
            "subject_type": row[2],
            "subject_id": row[3],
            "memory_kind": row[4],
            "content": content,
            "source": row[6],
            "status": row[7],
            "created_at": row[8].isoformat() if row[8] else None,
        })

    return results