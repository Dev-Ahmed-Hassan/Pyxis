-- Phase 6: explainable section-level semantic evidence with pgvector
-- Vectors are stored per resume section item and per concrete internship
-- requirement so semantic evidence can name the exact supporting text.

CREATE SCHEMA IF NOT EXISTS extensions;
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

CREATE TABLE public.resume_section_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resume_id UUID NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
    section_type TEXT NOT NULL
        CHECK (section_type IN ('summary', 'project', 'experience', 'education')),
    section_key TEXT NOT NULL,
    section_text TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    model_name TEXT NOT NULL,
    embedding extensions.vector(768) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (resume_id, section_type, section_key, model_name)
);

CREATE INDEX resume_section_embeddings_resume_model_idx
    ON public.resume_section_embeddings (resume_id, model_name);

CREATE TABLE public.internship_requirement_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    internship_input_id UUID NOT NULL
        REFERENCES public.internship_inputs(id) ON DELETE CASCADE,
    requirement_category TEXT NOT NULL
        CHECK (requirement_category IN ('required_skill', 'preferred_skill')),
    requirement TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    model_name TEXT NOT NULL,
    embedding extensions.vector(768) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (internship_input_id, requirement_category, requirement, model_name)
);

CREATE INDEX internship_requirement_embeddings_input_model_idx
    ON public.internship_requirement_embeddings (internship_input_id, model_name);

ALTER TABLE public.resume_section_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.internship_requirement_embeddings ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.resume_section_embeddings FROM anon, authenticated;
REVOKE ALL ON public.internship_requirement_embeddings FROM anon, authenticated;
