-- Migration 018: Interview Module Tables

CREATE TABLE public.interview_preparations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    match_analysis_id UUID NOT NULL REFERENCES public.match_analyses(id) ON DELETE CASCADE,
    match_explanation_id UUID REFERENCES public.match_explanations(id) ON DELETE SET NULL,
    github_evidence_id UUID REFERENCES public.github_match_evidence(id) ON DELETE SET NULL,
    preparation_version INTEGER NOT NULL,
    prompt_version INTEGER NOT NULL,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    request_payload JSONB NOT NULL,
    compact_context JSONB NOT NULL,
    preparation_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    stale_at TIMESTAMPTZ
);

CREATE INDEX interview_preparations_user_id_idx ON public.interview_preparations(user_id);
CREATE INDEX interview_preparations_match_analysis_id_idx ON public.interview_preparations(match_analysis_id);

CREATE TABLE public.interview_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    match_analysis_id UUID NOT NULL REFERENCES public.match_analyses(id) ON DELETE CASCADE,
    match_explanation_id UUID REFERENCES public.match_explanations(id) ON DELETE SET NULL,
    github_evidence_id UUID REFERENCES public.github_match_evidence(id) ON DELETE SET NULL,
    status TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    question_target INTEGER NOT NULL,
    focus_areas JSONB NOT NULL,
    compact_context JSONB NOT NULL,
    interview_plan JSONB NOT NULL,
    rolling_summary TEXT,
    current_question_number INTEGER NOT NULL DEFAULT 0,
    session_version INTEGER NOT NULL,
    prompt_version INTEGER NOT NULL,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    stale_at TIMESTAMPTZ
);

CREATE INDEX interview_sessions_user_id_idx ON public.interview_sessions(user_id);
CREATE INDEX interview_sessions_match_analysis_id_idx ON public.interview_sessions(match_analysis_id);

CREATE TABLE public.interview_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.interview_sessions(id) ON DELETE CASCADE,
    sequence_number INTEGER NOT NULL,
    category TEXT NOT NULL,
    question_text TEXT NOT NULL,
    reason TEXT NOT NULL,
    source_requirement TEXT,
    source_section_keys JSONB,
    is_follow_up BOOLEAN NOT NULL DEFAULT FALSE,
    parent_question_id UUID REFERENCES public.interview_questions(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX interview_questions_session_id_idx ON public.interview_questions(session_id);

CREATE TABLE public.interview_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.interview_sessions(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES public.interview_questions(id) ON DELETE CASCADE,
    answer_text TEXT NOT NULL,
    private_assessment JSONB NOT NULL,
    answered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX interview_answers_session_id_idx ON public.interview_answers(session_id);
CREATE INDEX interview_answers_question_id_idx ON public.interview_answers(question_id);

CREATE TABLE public.interview_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL UNIQUE REFERENCES public.interview_sessions(id) ON DELETE CASCADE,
    evaluation_version INTEGER NOT NULL,
    prompt_version INTEGER NOT NULL,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    evaluation_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX interview_evaluations_session_id_idx ON public.interview_evaluations(session_id);
