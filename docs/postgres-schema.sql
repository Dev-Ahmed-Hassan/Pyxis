-- Career assistant PostgreSQL / Supabase schema
-- Run this in the Supabase SQL Editor after removing the previous demo tables.
--
-- Development-only full reset:
-- DROP SCHEMA public CASCADE;
-- CREATE SCHEMA public;
-- GRANT ALL ON SCHEMA public TO postgres;
-- GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;

CREATE SCHEMA IF NOT EXISTS extensions;
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

CREATE TYPE public.user_role AS ENUM (
    'student',
    'admin'
);

CREATE TYPE public.resume_processing_status AS ENUM (
    'uploaded',
    'extracting_text',
    'text_extracted',
    'parsing',
    'validating',
    'embedding',
    'ready',
    'failed'
);

CREATE TYPE public.analysis_status AS ENUM (
    'queued',
    'processing',
    'complete',
    'failed',
    'stale'
);

CREATE TYPE public.skill_requirement_level AS ENUM (
    'required',
    'preferred',
    'mentioned'
);

CREATE TYPE public.skill_gap_importance AS ENUM (
    'core',
    'helpful',
    'minor'
);

CREATE TYPE public.application_status AS ENUM (
    'planned',
    'applied',
    'interviewing',
    'rejected',
    'accepted'
);

CREATE TYPE public.interview_status AS ENUM (
    'generated',
    'in_progress',
    'complete',
    'abandoned'
);

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TABLE public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role public.user_role NOT NULL DEFAULT 'student',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX users_email_unique_idx
    ON public.users (LOWER(email))
    WHERE deleted_at IS NULL;

CREATE TRIGGER users_set_updated_at
BEFORE UPDATE ON public.users
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE public.student_profiles (
    user_id UUID PRIMARY KEY REFERENCES public.users(id) ON DELETE CASCADE,
    headline TEXT,
    bio TEXT,
    target_roles TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER student_profiles_set_updated_at
BEFORE UPDATE ON public.student_profiles
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

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
    processing_attempts INTEGER NOT NULL DEFAULT 0
        CHECK (processing_attempts >= 0),
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    next_retry_at TIMESTAMPTZ,
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

CREATE INDEX resumes_user_id_idx ON public.resumes (user_id);

CREATE INDEX resumes_processing_queue_idx
    ON public.resumes (processing_status, next_retry_at, created_at)
    WHERE deleted_at IS NULL;

CREATE TRIGGER resumes_set_updated_at
BEFORE UPDATE ON public.resumes
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE public.internship_inputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT,
    company TEXT,
    description TEXT NOT NULL,
    application_url TEXT,
    mongo_document_id TEXT,
    extraction_status public.analysis_status NOT NULL DEFAULT 'queued',
    extraction_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX internship_inputs_user_id_idx
    ON public.internship_inputs (user_id);

CREATE TRIGGER internship_inputs_set_updated_at
BEFORE UPDATE ON public.internship_inputs
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE public.skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_name TEXT NOT NULL,
    category TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX skills_canonical_name_unique_idx
    ON public.skills (LOWER(canonical_name));

CREATE TABLE public.skill_aliases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_id UUID NOT NULL REFERENCES public.skills(id) ON DELETE CASCADE,
    alias TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX skill_aliases_alias_unique_idx
    ON public.skill_aliases (LOWER(alias));

CREATE INDEX skill_aliases_skill_id_idx
    ON public.skill_aliases (skill_id);

CREATE TABLE public.resume_skills (
    resume_id UUID NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES public.skills(id) ON DELETE CASCADE,
    confidence NUMERIC(4, 3) CHECK (confidence BETWEEN 0 AND 1),
    evidence TEXT,
    source TEXT NOT NULL DEFAULT 'extracted'
        CHECK (source IN ('extracted', 'manual')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (resume_id, skill_id)
);

CREATE INDEX resume_skills_skill_id_idx
    ON public.resume_skills (skill_id);

CREATE TRIGGER resume_skills_set_updated_at
BEFORE UPDATE ON public.resume_skills
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE public.internship_skills (
    internship_input_id UUID NOT NULL REFERENCES public.internship_inputs(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES public.skills(id) ON DELETE CASCADE,
    requirement_level public.skill_requirement_level NOT NULL,
    confidence NUMERIC(4, 3) CHECK (confidence BETWEEN 0 AND 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (internship_input_id, skill_id)
);

CREATE INDEX internship_skills_skill_id_idx
    ON public.internship_skills (skill_id);

-- The initial embedding contract is 384 dimensions, suitable for a lightweight
-- sentence-transformer model such as all-MiniLM-L6-v2. Changing the model or
-- dimensions later requires a deliberate migration and re-embedding pass.
CREATE TABLE public.resume_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
    section_type TEXT NOT NULL
        CHECK (section_type IN ('skills', 'projects', 'experience', 'education', 'summary')),
    model_name TEXT NOT NULL,
    embedding extensions.vector(384) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (resume_id, section_type, model_name)
);

CREATE INDEX resume_embeddings_resume_id_idx
    ON public.resume_embeddings (resume_id);

CREATE TRIGGER resume_embeddings_set_updated_at
BEFORE UPDATE ON public.resume_embeddings
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE public.internship_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    internship_input_id UUID NOT NULL REFERENCES public.internship_inputs(id) ON DELETE CASCADE,
    section_type TEXT NOT NULL DEFAULT 'description'
        CHECK (section_type IN ('description', 'required_skills', 'preferred_skills', 'responsibilities')),
    model_name TEXT NOT NULL,
    embedding extensions.vector(384) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (internship_input_id, section_type, model_name)
);

CREATE INDEX internship_embeddings_input_id_idx
    ON public.internship_embeddings (internship_input_id);

CREATE TRIGGER internship_embeddings_set_updated_at
BEFORE UPDATE ON public.internship_embeddings
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE public.analysis_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    internship_input_id UUID NOT NULL REFERENCES public.internship_inputs(id) ON DELETE CASCADE,
    status public.analysis_status NOT NULL DEFAULT 'queued',
    score_version TEXT NOT NULL,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX analysis_sessions_user_id_idx
    ON public.analysis_sessions (user_id);

CREATE INDEX analysis_sessions_internship_input_id_idx
    ON public.analysis_sessions (internship_input_id);

CREATE TRIGGER analysis_sessions_set_updated_at
BEFORE UPDATE ON public.analysis_sessions
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE public.resume_match_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_session_id UUID NOT NULL REFERENCES public.analysis_sessions(id) ON DELETE CASCADE,
    resume_id UUID NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
    internship_input_id UUID NOT NULL REFERENCES public.internship_inputs(id) ON DELETE CASCADE,
    overall_score NUMERIC(5, 2) NOT NULL CHECK (overall_score BETWEEN 0 AND 100),
    section_scores JSONB NOT NULL DEFAULT '{}',
    matched_skills JSONB NOT NULL DEFAULT '[]',
    missing_skills JSONB NOT NULL DEFAULT '[]',
    explanation TEXT,
    is_weak_match BOOLEAN NOT NULL DEFAULT FALSE,
    stale_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (analysis_session_id, resume_id)
);

CREATE INDEX resume_match_scores_resume_id_idx
    ON public.resume_match_scores (resume_id);

CREATE INDEX resume_match_scores_internship_input_id_idx
    ON public.resume_match_scores (internship_input_id);

CREATE TABLE public.skill_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_match_score_id UUID NOT NULL REFERENCES public.resume_match_scores(id) ON DELETE CASCADE,
    skill_id UUID NOT NULL REFERENCES public.skills(id) ON DELETE CASCADE,
    importance public.skill_gap_importance NOT NULL,
    roadmap JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (resume_match_score_id, skill_id)
);

CREATE INDEX skill_gaps_skill_id_idx
    ON public.skill_gaps (skill_id);

CREATE TABLE public.bookmarks (
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    internship_input_id UUID NOT NULL REFERENCES public.internship_inputs(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, internship_input_id)
);

CREATE TABLE public.application_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    internship_input_id UUID NOT NULL REFERENCES public.internship_inputs(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES public.resumes(id) ON DELETE SET NULL,
    status public.application_status NOT NULL DEFAULT 'planned',
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, internship_input_id)
);

CREATE TRIGGER application_tracking_set_updated_at
BEFORE UPDATE ON public.application_tracking
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE public.interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    resume_id UUID NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
    internship_input_id UUID NOT NULL REFERENCES public.internship_inputs(id) ON DELETE CASCADE,
    mongo_document_id TEXT,
    status public.interview_status NOT NULL DEFAULT 'generated',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX interview_sessions_user_id_idx
    ON public.interview_sessions (user_id);

CREATE TRIGGER interview_sessions_set_updated_at
BEFORE UPDATE ON public.interview_sessions
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TABLE public.ai_request_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    request_type TEXT NOT NULL,
    provider TEXT,
    model_name TEXT,
    success BOOLEAN NOT NULL,
    latency_ms INTEGER CHECK (latency_ms >= 0),
    error_type TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ai_request_logs_created_at_idx
    ON public.ai_request_logs (created_at DESC);

-- The FastAPI backend uses a private PostgreSQL connection. Browser clients
-- should not access these tables directly through Supabase's public API.
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.internship_inputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.skill_aliases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resume_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.internship_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resume_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.internship_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resume_match_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.skill_gaps ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bookmarks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.application_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_request_logs ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon, authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon, authenticated;
