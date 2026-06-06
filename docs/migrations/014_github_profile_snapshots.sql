-- Phase 14: raw GitHub profile snapshots.
-- This stores source GitHub API responses before any LLM portfolio analysis.

CREATE TABLE public.github_profile_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    github_username TEXT NOT NULL,
    profile_payload JSONB NOT NULL,
    repositories_payload JSONB NOT NULL DEFAULT '[]'::jsonb,
    languages_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    readmes_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    repository_limit INTEGER NOT NULL CHECK (repository_limit > 0),
    fetched_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX github_profile_snapshots_user_created_at_idx
    ON public.github_profile_snapshots (user_id, created_at DESC);

CREATE INDEX github_profile_snapshots_username_idx
    ON public.github_profile_snapshots (user_id, github_username, created_at DESC);

ALTER TABLE public.github_profile_snapshots ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.github_profile_snapshots FROM anon, authenticated;
