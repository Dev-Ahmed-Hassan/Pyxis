from typing import Literal

from pydantic import Field

from services.ai.schemas import StrictSchema

MatchExplanationVerdict = Literal[
    "strong_match",
    "good_match",
    "moderate_match",
    "weak_match",
    "low_match",
]
ExplanationImpact = Literal["high", "medium", "low"]
ExplanationConfidence = Literal["high", "medium", "low"]
GapSeverity = Literal["high", "medium", "low"]
ResumeImprovementType = Literal[
    "clarify_existing_project",
    "add_missing_detail",
    "move_skill_into_project",
    "add_learning_project",
    "add_certification_context",
    "no_action_needed",
]


class MatchExplanationScoreCardOutput(StrictSchema):
    base_score: float = Field(ge=0.0, le=100.0)
    ai_reviewed_score: float | None = Field(default=None, ge=0.0, le=100.0)
    adjustment_points: float | None = None
    verdict: MatchExplanationVerdict
    headline: str
    summary: str


class MatchExplanationStrengthOutput(StrictSchema):
    requirement: str
    title: str
    impact: ExplanationImpact
    evidence_section_keys: list[str]
    explanation: str
    confidence: ExplanationConfidence


class MatchExplanationPartialMatchOutput(StrictSchema):
    requirement: str
    title: str
    support_level: Literal["strong_partial", "weak_related"]
    evidence_section_keys: list[str]
    explanation: str
    missing_detail: str
    confidence: ExplanationConfidence


class MatchExplanationGapOutput(StrictSchema):
    requirement: str
    severity: GapSeverity
    reason: str
    why_it_matters: str
    recommended_action: str


class MatchExplanationResumeImprovementOutput(StrictSchema):
    type: ResumeImprovementType
    requirement: str
    suggestion: str
    why_it_matters: str
    evidence_section_keys: list[str]


class MatchExplanationLearningProjectOutput(StrictSchema):
    requirement: str
    title: str
    goal: str
    tools: list[str]
    steps: list[str]
    resume_outcome: str


class MatchExplanationInterviewTalkingPointOutput(StrictSchema):
    requirement: str
    prompt: str
    evidence_section_keys: list[str]


class MatchExplanationFairnessNoteOutput(StrictSchema):
    assessment: Literal[
        "fair",
        "potentially_underestimated",
        "potentially_overestimated",
        "needs_manual_review",
    ]
    note: str
    related_requirements: list[str]


class LlmMatchExplanationOutput(StrictSchema):
    score_card: MatchExplanationScoreCardOutput
    strengths: list[MatchExplanationStrengthOutput]
    partial_matches: list[MatchExplanationPartialMatchOutput]
    gaps: list[MatchExplanationGapOutput]
    resume_improvements: list[MatchExplanationResumeImprovementOutput]
    learning_projects: list[MatchExplanationLearningProjectOutput]
    interview_talking_points: list[MatchExplanationInterviewTalkingPointOutput]
    fairness_notes: list[MatchExplanationFairnessNoteOutput]
