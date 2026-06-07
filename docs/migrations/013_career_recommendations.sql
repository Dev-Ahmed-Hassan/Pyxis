-- Phase 13: saved profile-level career path recommendations.
-- Recommendations are generated from profile facts and retrieved career
-- guidance so the app can reuse results without repeated AI generation.

CREATE TABLE public.career_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    recommendation_version TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    target_field TEXT,
    preferred_roles TEXT[] NOT NULL DEFAULT '{}',
    profile_snapshot JSONB NOT NULL,
    retrieved_knowledge_chunks JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommendation_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    stale_at TIMESTAMPTZ
);

CREATE INDEX career_recommendations_user_created_at_idx
    ON public.career_recommendations (user_id, created_at DESC);

CREATE INDEX career_recommendations_target_idx
    ON public.career_recommendations (user_id, target_field, created_at DESC);

ALTER TABLE public.career_recommendations ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.career_recommendations FROM anon, authenticated;
