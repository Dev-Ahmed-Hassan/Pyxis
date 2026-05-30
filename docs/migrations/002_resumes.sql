-- Phase 3: resume metadata management

CREATE TYPE public.resume_processing_status AS ENUM (
    'uploaded',
    'extracting_text',
    'parsing',
    'validating',
    'embedding',
    'ready',
    'failed'
);

CREATE TABLE public.resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    alias TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL CHECK (file_size_bytes > 0),
    storage_path TEXT,
    mongo_document_id TEXT,
    processing_status public.resume_processing_status NOT NULL DEFAULT 'uploaded',
    parser_version TEXT,
    processing_error TEXT,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX resumes_user_alias_unique_idx
    ON public.resumes (user_id, LOWER(alias))
    WHERE deleted_at IS NULL;

CREATE UNIQUE INDEX resumes_one_default_per_user_idx
    ON public.resumes (user_id)
    WHERE is_default = TRUE AND deleted_at IS NULL;

CREATE INDEX resumes_user_id_idx
    ON public.resumes (user_id);

CREATE TRIGGER resumes_set_updated_at
BEFORE UPDATE ON public.resumes
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

ALTER TABLE public.resumes ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.resumes FROM anon, authenticated;
