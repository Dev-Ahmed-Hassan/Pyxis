-- Phase 17: saved match-specific GitHub evidence.
-- This is separate from profile-level GitHub analysis. It connects one saved
-- resume-to-internship match analysis with one GitHub snapshot and stores the
-- role-specific interpretation for the match dashboard and interview prep.

CREATE TABLE public.github_match_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    match_analysis_id UUID NOT NULL REFERENCES public.match_analyses(id) ON DELETE CASCADE,
    github_snapshot_id UUID NOT NULL REFERENCES public.github_profile_snapshots(id) ON DELETE CASCADE,
    evidence_version TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    evidence_request JSONB NOT NULL DEFAULT '{}'::jsonb,
    compact_context_used JSONB NOT NULL,
    evidence_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    stale_at TIMESTAMPTZ
);

CREATE INDEX github_match_evidence_user_created_at_idx
    ON public.github_match_evidence (user_id, created_at DESC);

CREATE INDEX github_match_evidence_match_created_at_idx
    ON public.github_match_evidence (match_analysis_id, created_at DESC);

CREATE INDEX github_match_evidence_snapshot_created_at_idx
    ON public.github_match_evidence (github_snapshot_id, created_at DESC);

ALTER TABLE public.github_match_evidence ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.github_match_evidence FROM anon, authenticated;
