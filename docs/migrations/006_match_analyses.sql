-- Phase 5: immutable versioned resume-to-internship match-analysis history
-- Each row stores the complete calculated breakdown so historical results
-- remain auditable after scoring rules evolve.

CREATE TABLE public.match_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    resume_id UUID NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
    internship_input_id UUID NOT NULL
        REFERENCES public.internship_inputs(id) ON DELETE CASCADE,
    analysis_session_id UUID NOT NULL DEFAULT gen_random_uuid(),
    score_version TEXT NOT NULL,
    overall_score NUMERIC(5, 2) NOT NULL
        CHECK (overall_score BETWEEN 0 AND 100),
    analysis_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    stale_at TIMESTAMPTZ
);

CREATE INDEX match_analyses_user_created_at_idx
    ON public.match_analyses (user_id, created_at DESC);

CREATE INDEX match_analyses_session_idx
    ON public.match_analyses (user_id, analysis_session_id, created_at DESC);

CREATE INDEX match_analyses_inputs_idx
    ON public.match_analyses (resume_id, internship_input_id, created_at DESC);

ALTER TABLE public.match_analyses ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.match_analyses FROM anon, authenticated;
