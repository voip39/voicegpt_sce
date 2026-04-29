from typing import Any

from runtime.db import get_conn
from memory.embeddings import embed_text
from memory.render import render_memory_content


def index_memory_item(
    memory_item_id: int,
    subject_type: str,
    subject_id: str,
    content: dict[str, Any],
    embedding_model: str = "text-embedding-3-small",
) -> dict[str, Any]:
    content_text = render_memory_content(content)
    if not content_text:
        raise ValueError("cannot index empty memory content")

    vector = embed_text(content_text, model=embedding_model)

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO runtime.memory_embeddings
                (memory_item_id, subject_type, subject_id, embedding_model, embedding, content_text)
                VALUES (%s, %s, %s, %s, %s::vector, %s)
                ON CONFLICT (memory_item_id)
                DO UPDATE SET
                    embedding_model = EXCLUDED.embedding_model,
                    embedding = EXCLUDED.embedding,
                    content_text = EXCLUDED.content_text
                RETURNING id, memory_item_id, subject_type, subject_id, embedding_model, content_text, created_at
                """,
                (
                    memory_item_id,
                    subject_type,
                    subject_id,
                    embedding_model,
                    str(vector),
                    content_text,
                ),
            )
            row = cur.fetchone()
            conn.commit()

    return {
        "id": row[0],
        "memory_item_id": row[1],
        "subject_type": row[2],
        "subject_id": row[3],
        "embedding_model": row[4],
        "content_text": row[5],
        "created_at": row[6].isoformat() if row[6] else None,
    }
