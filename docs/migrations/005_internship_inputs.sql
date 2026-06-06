-- Phase 4: internship-description input and durable parsing queue
-- Students paste internship descriptions. The API stores them quickly and a
-- background worker parses structured requirements without blocking requests.

CREATE TYPE public.internship_processing_status AS ENUM (
    'submitted',
    'parsing',
    'validating',
    'ready',
    'failed'
);

CREATE TABLE public.internship_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    original_description TEXT NOT NULL
        CHECK (CHAR_LENGTH(original_description) BETWEEN 50 AND 20000),
    application_url TEXT,
    mongo_document_id TEXT,
    processing_status public.internship_processing_status NOT NULL DEFAULT 'submitted',
    parser_version TEXT,
    processing_error TEXT,
    processing_attempts INTEGER NOT NULL DEFAULT 0
        CHECK (processing_attempts >= 0),
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    next_retry_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX internship_inputs_user_id_idx
    ON public.internship_inputs (user_id);

CREATE INDEX internship_inputs_processing_queue_idx
    ON public.internship_inputs (processing_status, next_retry_at, created_at)
    WHERE deleted_at IS NULL;

CREATE TRIGGER internship_inputs_set_updated_at
BEFORE UPDATE ON public.internship_inputs
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.internship_inputs ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.internship_inputs FROM anon, authenticated;
