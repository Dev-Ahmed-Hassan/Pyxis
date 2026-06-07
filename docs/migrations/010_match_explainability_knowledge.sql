-- Phase 10: RAG knowledge chunks for match explainability.
-- These rows store global guidance chunks, not student resume evidence.

CREATE SCHEMA IF NOT EXISTS extensions;
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

CREATE TABLE public.match_explainability_knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    namespace TEXT NOT NULL DEFAULT 'match_explainability',
    source_path TEXT NOT NULL,
    heading TEXT NOT NULL,
    heading_path TEXT NOT NULL,
    topic_tags TEXT[] NOT NULL DEFAULT '{}',
    chunk_text TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    model_name TEXT NOT NULL,
    embedding extensions.vector(768) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (namespace, source_path, heading_path, model_name)
);

CREATE INDEX match_explainability_chunks_namespace_model_idx
    ON public.match_explainability_knowledge_chunks (namespace, model_name);

CREATE INDEX match_explainability_chunks_source_idx
    ON public.match_explainability_knowledge_chunks (source_path);

CREATE INDEX match_explainability_chunks_tags_idx
    ON public.match_explainability_knowledge_chunks USING GIN (topic_tags);

ALTER TABLE public.match_explainability_knowledge_chunks ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.match_explainability_knowledge_chunks FROM anon, authenticated;
