CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS runtime.memory_embeddings (
    id BIGSERIAL PRIMARY KEY,
    memory_item_id BIGINT NOT NULL REFERENCES runtime.memory_items(id) ON DELETE CASCADE,
    subject_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    content_text TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_memory_embeddings_memory_item_id
ON runtime.memory_embeddings(memory_item_id);

CREATE INDEX IF NOT EXISTS idx_memory_embeddings_subject
ON runtime.memory_embeddings(subject_type, subject_id);
