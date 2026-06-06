-- Phase 7: durable retry queue for asynchronous semantic embedding refresh
-- Parsed profiles remain usable when the embedding provider or pgvector is
-- temporarily unavailable. One queued row represents the latest source state.

CREATE TYPE public.semantic_embedding_refresh_status AS ENUM (
    'queued',
    'processing',
    'retrying',
    'complete',
    'failed'
);

CREATE TABLE public.semantic_embedding_refresh_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID REFERENCES public.resumes(id) ON DELETE CASCADE,
    internship_input_id UUID REFERENCES public.internship_inputs(id) ON DELETE CASCADE,
    generation UUID NOT NULL DEFAULT gen_random_uuid(),
    status public.semantic_embedding_refresh_status NOT NULL DEFAULT 'queued',
    processing_attempts INTEGER NOT NULL DEFAULT 0
        CHECK (processing_attempts >= 0),
    processing_error TEXT,
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    next_retry_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        (resume_id IS NOT NULL AND internship_input_id IS NULL)
        OR
        (resume_id IS NULL AND internship_input_id IS NOT NULL)
    )
);

CREATE UNIQUE INDEX semantic_embedding_refresh_jobs_resume_unique_idx
    ON public.semantic_embedding_refresh_jobs (resume_id)
    WHERE resume_id IS NOT NULL;

CREATE UNIQUE INDEX semantic_embedding_refresh_jobs_internship_unique_idx
    ON public.semantic_embedding_refresh_jobs (internship_input_id)
    WHERE internship_input_id IS NOT NULL;

CREATE INDEX semantic_embedding_refresh_jobs_queue_idx
    ON public.semantic_embedding_refresh_jobs (status, next_retry_at, created_at)
    WHERE status IN ('queued', 'processing', 'retrying');

CREATE TRIGGER semantic_embedding_refresh_jobs_set_updated_at
BEFORE UPDATE ON public.semantic_embedding_refresh_jobs
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.semantic_embedding_refresh_jobs ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.semantic_embedding_refresh_jobs FROM anon, authenticated;
