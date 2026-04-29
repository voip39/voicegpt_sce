from typing import Any, Dict, List

from runtime.db import get_conn
from memory.embeddings import embed_text


def semantic_memory_search(
    subject_type: str,
    subject_id: str,
    query_text: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    vector = embed_text(query_text)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    me.id,
                    me.memory_item_id,
                    me.content_text,
                    me.embedding_model,
                    mi.memory_id,
                    mi.memory_kind,
                    mi.content,
                    mi.source,
                    mi.status,
                    mi.created_at,
                    1 - (me.embedding <=> %s::vector) AS similarity
                FROM runtime.memory_embeddings me
                JOIN runtime.memory_items mi
                  ON mi.id = me.memory_item_id
                WHERE me.subject_type = %s
                  AND me.subject_id = %s
                  AND mi.status = 'active'
                ORDER BY me.embedding <=> %s::vector
                LIMIT %s
                """,
                (
                    str(vector),
                    subject_type,
                    subject_id,
                    str(vector),
                    limit,
                ),
            )
            rows = cur.fetchall()

    results = []
    for row in rows:
        results.append({
            "embedding_row_id": row[0],
            "memory_item_id": row[1],
            "content_text": row[2],
            "embedding_model": row[3],
            "memory_id": row[4],
            "memory_kind": row[5],
            "content": row[6],
            "source": row[7],
            "status": row[8],
            "created_at": row[9].isoformat() if row[9] else None,
            "similarity": float(row[10]) if row[10] is not None else None,
        })

    return results
