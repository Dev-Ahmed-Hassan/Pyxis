-- Phase 16: saved LLM portfolio analyses for GitHub profile snapshots.
-- Raw and compact snapshots remain the source data; this table stores the
-- UI-facing interpretation so GitHub analysis can be reused without repeated
-- AI calls.

CREATE TABLE public.github_profile_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    snapshot_id UUID NOT NULL REFERENCES public.github_profile_snapshots(id) ON DELETE CASCADE,
    analysis_version TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    analysis_request JSONB NOT NULL DEFAULT '{}'::jsonb,
    compact_snapshot_used JSONB NOT NULL,
    analysis_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    stale_at TIMESTAMPTZ
);

CREATE INDEX github_profile_analyses_user_created_at_idx
    ON public.github_profile_analyses (user_id, created_at DESC);

CREATE INDEX github_profile_analyses_snapshot_created_at_idx
    ON public.github_profile_analyses (snapshot_id, created_at DESC);

ALTER TABLE public.github_profile_analyses ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.github_profile_analyses FROM anon, authenticated;
