import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Shared literal types
# ---------------------------------------------------------------------------

InterviewDifficulty = Literal["beginner", "intermediate", "advanced"]
InterviewMode = Literal["preparation", "live"]
InterviewStatus = Literal["created", "in_progress", "completed", "abandoned"]
InterviewQuestionCategory = Literal[
    "role_technical",
    "resume_project",
    "experience",
    "gap_validation",
    "behavioral",
    "situational",
    "github_project",
]
InterviewFocusArea = Literal["technical", "resume", "behavioral", "situational", "github"]

# ---------------------------------------------------------------------------
# Preparation Mode Schemas
# ---------------------------------------------------------------------------


class InterviewPreparationCreate(BaseModel):
    match_analysis_id: uuid.UUID
    match_explanation_id: uuid.UUID | None = None
    github_evidence_id: uuid.UUID | None = None
    difficulty: InterviewDifficulty = "intermediate"
    question_count: int = Field(default=12, ge=5, le=20)
    focus_areas: list[InterviewFocusArea] = Field(default=["technical", "resume", "behavioral"])
    force_refresh: bool = False


class InterviewPreparationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    match_analysis_id: uuid.UUID
    match_explanation_id: uuid.UUID | None
    github_evidence_id: uuid.UUID | None
    preparation_version: int
    prompt_version: int
    provider: str
    model_name: str
    compact_context: dict
    preparation_payload: dict
    created_at: datetime
    stale_at: datetime | None


# ---------------------------------------------------------------------------
# Live Session Schemas
# ---------------------------------------------------------------------------


class InterviewSessionCreate(BaseModel):
    match_analysis_id: uuid.UUID
    match_explanation_id: uuid.UUID | None = None
    github_evidence_id: uuid.UUID | None = None
    difficulty: InterviewDifficulty = "intermediate"
    question_count: int = Field(default=10, ge=5, le=20)
    focus_areas: list[InterviewFocusArea] = Field(default=["technical", "resume", "behavioral"])


class InterviewSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    match_analysis_id: uuid.UUID
    match_explanation_id: uuid.UUID | None
    github_evidence_id: uuid.UUID | None
    status: InterviewStatus
    difficulty: InterviewDifficulty
    question_target: int
    focus_areas: list[str]
    current_question_number: int
    session_version: int
    provider: str
    model_name: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    stale_at: datetime | None


# ---------------------------------------------------------------------------
# Question Schemas
# ---------------------------------------------------------------------------


class InterviewQuestionResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    sequence_number: int
    category: InterviewQuestionCategory
    question_text: str
    reason: str
    is_follow_up: bool
    parent_question_id: uuid.UUID | None
    created_at: datetime


class NextQuestionResponse(BaseModel):
    question: InterviewQuestionResponse
    # Neutral signal — does NOT reveal private assessment details
    is_follow_up: bool
    questions_remaining: int


# ---------------------------------------------------------------------------
# Answer Schemas
# ---------------------------------------------------------------------------


class InterviewAnswerSubmit(BaseModel):
    question_id: uuid.UUID
    # Limit answer size as required by Section 11 (Safety)
    answer_text: str = Field(min_length=10, max_length=4000)


class InterviewAnswerAcknowledgement(BaseModel):
    """Returned after answer submission. Never exposes private_assessment."""
    answer_id: uuid.UUID
    session_id: uuid.UUID
    next_is_follow_up: bool
    session_complete: bool


# ---------------------------------------------------------------------------
# Evaluation Schemas (Section 7 of handoff)
# ---------------------------------------------------------------------------


class InterviewCategoryScore(BaseModel):
    category: str
    score: float
    strengths: list[str]
    improvements: list[str]


class InterviewQuestionReview(BaseModel):
    question_id: uuid.UUID
    question: str
    answer_summary: str
    score: float
    what_went_well: list[str]
    what_was_missing: list[str]
    better_answer_approach: str


class InterviewEvaluationPayload(BaseModel):
    overall_score: float
    verdict: str
    summary: str
    category_scores: list[InterviewCategoryScore]
    question_reviews: list[InterviewQuestionReview]
    demonstrated_strengths: list[str]
    knowledge_gaps: list[str]
    communication_feedback: list[str]
    unsupported_claims: list[str]
    recommended_revision_topics: list[str]
    next_actions: list[str]


class InterviewEvaluationResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    evaluation_version: int
    prompt_version: int
    provider: str
    model_name: str
    evaluation: InterviewEvaluationPayload
    created_at: datetime
