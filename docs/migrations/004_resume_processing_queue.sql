-- Phase 3: durable resume-processing queue metadata
-- PostgreSQL stores pending work so processing can resume after backend restarts.

ALTER TABLE public.resumes
ADD COLUMN processing_attempts INTEGER NOT NULL DEFAULT 0
    CHECK (processing_attempts >= 0),
ADD COLUMN processing_started_at TIMESTAMPTZ,
ADD COLUMN processing_completed_at TIMESTAMPTZ,
ADD COLUMN next_retry_at TIMESTAMPTZ;

CREATE INDEX resumes_processing_queue_idx
    ON public.resumes (processing_status, next_retry_at, created_at)
    WHERE deleted_at IS NULL;
