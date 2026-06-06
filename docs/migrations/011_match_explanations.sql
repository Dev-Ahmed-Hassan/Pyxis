-- Phase 11: saved RAG-assisted match explanations and improvement plans.
-- These rows preserve the generated student-facing explanation for a saved
-- match analysis and optional LLM adjudication so the app can reuse results
-- without paying for repeated AI generation.

CREATE TABLE public.match_explanations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    resume_id UUID NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
    internship_input_id UUID NOT NULL
        REFERENCES public.internship_inputs(id) ON DELETE CASCADE,
    match_analysis_id UUID NOT NULL
        REFERENCES public.match_analyses(id) ON DELETE CASCADE,
    match_llm_adjudication_id UUID
        REFERENCES public.match_llm_adjudications(id) ON DELETE SET NULL,
    explanation_version TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    score_version TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    base_score NUMERIC(5, 2) NOT NULL
        CHECK (base_score BETWEEN 0 AND 100),
    ai_reviewed_score NUMERIC(5, 2)
        CHECK (ai_reviewed_score IS NULL OR ai_reviewed_score BETWEEN 0 AND 100),
    ai_adjustment_points NUMERIC(5, 2),
    retrieved_knowledge_chunks JSONB NOT NULL DEFAULT '[]'::jsonb,
    explanation_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    stale_at TIMESTAMPTZ
);

CREATE INDEX match_explanations_user_created_at_idx
    ON public.match_explanations (user_id, created_at DESC);

CREATE INDEX match_explanations_inputs_idx
    ON public.match_explanations
    (resume_id, internship_input_id, created_at DESC);

CREATE INDEX match_explanations_analysis_idx
    ON public.match_explanations
    (match_analysis_id, created_at DESC);

CREATE INDEX match_explanations_adjudication_idx
    ON public.match_explanations
    (match_llm_adjudication_id, created_at DESC)
    WHERE match_llm_adjudication_id IS NOT NULL;

CREATE UNIQUE INDEX match_explanations_active_analysis_adjudication_idx
    ON public.match_explanations (
        match_analysis_id,
        COALESCE(
            match_llm_adjudication_id,
            '00000000-0000-0000-0000-000000000000'::uuid
        ),
        explanation_version
    )
    WHERE stale_at IS NULL;

ALTER TABLE public.match_explanations ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.match_explanations FROM anon, authenticated;
