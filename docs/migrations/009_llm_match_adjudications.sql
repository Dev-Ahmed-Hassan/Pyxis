-- Phase 7: retrieval-assisted LLM evidence adjudication in shadow mode.
-- The deterministic score remains official. These immutable rows retain the
-- model, prompt version, retrieved passages, cited judgments, and shadow score.

ALTER TABLE public.internship_requirement_embeddings
    ADD COLUMN requirement_text TEXT;

UPDATE public.internship_requirement_embeddings
SET requirement_text = requirement
WHERE requirement_text IS NULL;

ALTER TABLE public.internship_requirement_embeddings
    ALTER COLUMN requirement_text SET NOT NULL;

ALTER TABLE public.resume_section_embeddings
    DROP CONSTRAINT resume_section_embeddings_section_type_check;

ALTER TABLE public.resume_section_embeddings
    ADD CONSTRAINT resume_section_embeddings_section_type_check
    CHECK (
        section_type IN (
            'skills_list',
            'summary',
            'project',
            'experience',
            'education',
            'certification'
        )
    );

CREATE TABLE public.match_llm_adjudications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    resume_id UUID NOT NULL REFERENCES public.resumes(id) ON DELETE CASCADE,
    internship_input_id UUID NOT NULL
        REFERENCES public.internship_inputs(id) ON DELETE CASCADE,
    adjudication_version TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    score_version TEXT NOT NULL,
    official_score NUMERIC(5, 2) NOT NULL
        CHECK (official_score BETWEEN 0 AND 100),
    shadow_score NUMERIC(5, 2) NOT NULL
        CHECK (shadow_score BETWEEN 0 AND 100),
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    adjudication_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    stale_at TIMESTAMPTZ
);

CREATE INDEX match_llm_adjudications_user_created_at_idx
    ON public.match_llm_adjudications (user_id, created_at DESC);

CREATE INDEX match_llm_adjudications_inputs_idx
    ON public.match_llm_adjudications
    (resume_id, internship_input_id, created_at DESC);

ALTER TABLE public.match_llm_adjudications ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON public.match_llm_adjudications FROM anon, authenticated;
