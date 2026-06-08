"""
AI structured output schemas for the Interview Module.

Six separate schemas as required by Section 10 of the handoff:
  1. Preparation generation
  2. Live interview plan
  3. Next-question decision
  4. Private answer assessment
  5. Rolling summary update
  6. Final collective evaluation

All classes inherit from StrictSchema (extra="forbid") so any unexpected
field the LLM hallucinates causes immediate rejection and fallback.
"""

from typing import Literal

from pydantic import Field

from services.ai.schemas import StrictSchema

# ---------------------------------------------------------------------------
# Shared types
# ---------------------------------------------------------------------------

InterviewQuestionCategory = Literal[
    "role_technical",
    "resume_project",
    "experience",
    "gap_validation",
    "behavioral",
    "situational",
    "github_project",
]

# ---------------------------------------------------------------------------
# Schema 1: Preparation Generation
# Used by: interview_preparation_service.py
# Purpose: Full prep packet returned after POST /interviews/preparations
# ---------------------------------------------------------------------------


class PreparationQuestionOutput(StrictSchema):
    category: InterviewQuestionCategory
    question_text: str
    why_relevant: str
    answer_structure: str
    grounded_evidence: list[str]
    common_mistakes: list[str]
    follow_up_questions: list[str]


class InterviewPreparationOutput(StrictSchema):
    interview_overview: str
    likely_focus: str
    questions: list[PreparationQuestionOutput]
    preparation_checklist: list[str]


# ---------------------------------------------------------------------------
# Schema 2: Live Interview Plan
# Used by: interview_session_service.py (create_session)
# Purpose: The hidden question plan generated when a live session starts.
#          The user never sees this directly — it is the session's "script".
# ---------------------------------------------------------------------------


class PlannedQuestionOutput(StrictSchema):
    sequence_number: int
    category: InterviewQuestionCategory
    question_text: str
    reason: str
    source_requirement: str | None = None


class InterviewPlanOutput(StrictSchema):
    plan_summary: str
    planned_questions: list[PlannedQuestionOutput]


# ---------------------------------------------------------------------------
# Schema 3: Next-Question Decision
# Used by: interview_session_service.py (get_next_question)
# Purpose: After each answer, the AI decides whether to ask an adaptive
#          follow-up or advance to the next planned question.
# ---------------------------------------------------------------------------


class NextQuestionDecisionOutput(StrictSchema):
    decision: Literal["follow_up", "next_planned"]
    follow_up_question_text: str | None = None
    follow_up_category: InterviewQuestionCategory | None = None
    follow_up_reason: str | None = None


# ---------------------------------------------------------------------------
# Schema 4: Private Answer Assessment
# Used by: interview_session_service.py (submit_answer)
# Purpose: Hidden per-turn scoring stored in interview_answers.private_assessment.
#          NEVER returned to the user until the session is complete.
# ---------------------------------------------------------------------------


class PrivateAnswerAssessmentOutput(StrictSchema):
    relevance: Literal["high", "medium", "low"]
    technical_correctness: Literal["correct", "mostly_correct", "partially_correct", "incorrect", "not_applicable"]
    evidence_usage: Literal["strong", "moderate", "weak", "none"]
    clarity: Literal["clear", "mostly_clear", "unclear"]
    confidence_level: Literal["high", "medium", "low"]
    contradictions_or_unsupported_claims: list[str]
    follow_up_needed: bool
    evaluator_notes: str


# ---------------------------------------------------------------------------
# Schema 5: Rolling Summary Update
# Used by: interview_session_service.py (submit_answer)
# Purpose: After each answer the rolling_summary in the DB is rewritten to
#          compress old turns. This keeps the prompt size bounded.
# ---------------------------------------------------------------------------


class RollingSummaryOutput(StrictSchema):
    updated_summary: str


# ---------------------------------------------------------------------------
# Schema 6: Final Collective Evaluation
# Used by: interview_evaluation_service.py (complete_session)
# Purpose: The user-facing final report card. Maps directly to
#          InterviewEvaluationPayload in schemas/interview.py.
# ---------------------------------------------------------------------------


class CategoryScoreOutput(StrictSchema):
    category: str
    score: float = Field(ge=0.0, le=100.0)
    strengths: list[str]
    improvements: list[str]


class QuestionReviewOutput(StrictSchema):
    question_id: str  # stored as str; service converts to UUID
    question: str
    answer_summary: str
    score: float = Field(ge=0.0, le=100.0)
    what_went_well: list[str]
    what_was_missing: list[str]
    better_answer_approach: str


class FinalEvaluationOutput(StrictSchema):
    overall_score: float = Field(ge=0.0, le=100.0)
    verdict: str
    summary: str
    category_scores: list[CategoryScoreOutput]
    question_reviews: list[QuestionReviewOutput]
    demonstrated_strengths: list[str]
    knowledge_gaps: list[str]
    communication_feedback: list[str]
    unsupported_claims: list[str]
    recommended_revision_topics: list[str]
    next_actions: list[str]
