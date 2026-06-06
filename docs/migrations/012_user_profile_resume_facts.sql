-- Phase 12: profile-level facts extracted from saved parsed resumes.
-- Every fact keeps resume_id so deleting or reparsing one resume can remove
-- only the facts that came from that resume.

CREATE TABLE public.user_profile_skill_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    resume_id UUID NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    source_section TEXT NOT NULL
        CHECK (source_section IN ('skills_list', 'project', 'experience', 'certification')),
    source_key TEXT NOT NULL,
    extraction_source TEXT NOT NULL
        CHECK (extraction_source IN ('explicit', 'inferred', 'manual')),
    confidence NUMERIC(4, 3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    evidence TEXT,
    context TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX user_profile_skill_sources_user_idx
    ON public.user_profile_skill_sources (user_id, canonical_name);

CREATE INDEX user_profile_skill_sources_resume_idx
    ON public.user_profile_skill_sources (resume_id);

CREATE TABLE public.user_profile_project_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    resume_id UUID NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
    source_key TEXT NOT NULL,
    project_name TEXT,
    description JSONB NOT NULL DEFAULT '[]'::jsonb,
    skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence NUMERIC(4, 3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    evidence TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (resume_id, source_key)
);

CREATE INDEX user_profile_project_sources_user_idx
    ON public.user_profile_project_sources (user_id);

CREATE INDEX user_profile_project_sources_resume_idx
    ON public.user_profile_project_sources (resume_id);

CREATE TABLE public.user_profile_certification_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    resume_id UUID NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
    source_key TEXT NOT NULL,
    certification_name TEXT NOT NULL,
    issuer TEXT,
    date TEXT,
    confidence NUMERIC(4, 3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    evidence TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (resume_id, source_key)
);

CREATE INDEX user_profile_certification_sources_user_idx
    ON public.user_profile_certification_sources (user_id);

CREATE INDEX user_profile_certification_sources_resume_idx
    ON public.user_profile_certification_sources (resume_id);

ALTER TABLE public.user_profile_skill_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profile_project_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_profile_certification_sources ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.user_profile_skill_sources FROM anon, authenticated;
REVOKE ALL ON public.user_profile_project_sources FROM anon, authenticated;
REVOKE ALL ON public.user_profile_certification_sources FROM anon, authenticated;
