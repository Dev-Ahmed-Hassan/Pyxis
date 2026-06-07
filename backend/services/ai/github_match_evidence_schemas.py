from typing import Literal

from services.ai.schemas import StrictSchema

EvidenceStrength = Literal["strong", "moderate", "weak"]
RequirementSupportLevel = Literal["direct", "partial", "adjacent", "none"]
Priority = Literal["high", "medium", "low"]


class GitHubMatchedRepositoryOutput(StrictSchema):
    repository_name: str
    url: str | None
    evidence_strength: EvidenceStrength
    relevant_requirements: list[str]
    demonstrated_skills: list[str]
    why_it_supports_this_match: str
    application_use: str
    interview_use: str
    improvement_note: str


class GitHubRequirementSupportOutput(StrictSchema):
    requirement: str
    support_level: RequirementSupportLevel
    supporting_repositories: list[str]
    explanation: str
    remaining_gap: str


class GitHubMatchActionOutput(StrictSchema):
    title: str
    priority: Priority
    reason: str
    steps: list[str]


class GitHubInterviewQuestionOutput(StrictSchema):
    repository_name: str
    requirement: str
    question: str
    strong_answer_hint: str


class LlmGitHubMatchEvidenceOutput(StrictSchema):
    headline: str
    summary: str
    overall_support_level: EvidenceStrength
    matched_repositories: list[GitHubMatchedRepositoryOutput]
    requirement_support: list[GitHubRequirementSupportOutput]
    application_talking_points: list[str]
    interview_questions: list[GitHubInterviewQuestionOutput]
    improvement_actions: list[GitHubMatchActionOutput]
    limitations: list[str]
