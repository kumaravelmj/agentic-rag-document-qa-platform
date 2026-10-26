-- Keep JSON columns compatible with GIN indexes on both fresh and older schemas.
ALTER TABLE document_chunks
    ALTER COLUMN keywords TYPE jsonb USING keywords::jsonb,
    ALTER COLUMN metadata TYPE jsonb USING metadata::jsonb;

ALTER TABLE documents
    ALTER COLUMN metadata TYPE jsonb USING metadata::jsonb;

-- Full-text search support for document_chunks (keyword retrieval).
ALTER TABLE document_chunks
    ADD COLUMN IF NOT EXISTS content_tsv tsvector
    GENERATED ALWAYS AS (to_tsvector('english', coalesce(content, ''))) STORED;

CREATE INDEX IF NOT EXISTS ix_document_chunks_content_tsv
    ON document_chunks USING GIN (content_tsv);

CREATE INDEX IF NOT EXISTS ix_document_chunks_keywords
    ON document_chunks USING GIN (keywords);

CREATE INDEX IF NOT EXISTS ix_document_chunks_metadata
    ON document_chunks USING GIN (metadata);

CREATE INDEX IF NOT EXISTS ix_documents_metadata
    ON documents USING GIN (metadata);

-- Vector similarity index (cosine distance).
CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw
    ON document_chunks USING hnsw (embedding vector_cosine_ops);
