from typing import Literal

from pydantic import Field

from services.ai.schemas import StrictSchema

GitHubEvidenceLevel = Literal["strong", "moderate", "weak"]
GitHubPriority = Literal["high", "medium", "low"]


class GitHubTechnologySummaryOutput(StrictSchema):
    top_languages: list[str]
    detected_frameworks_or_tools: list[str]
    likely_skill_areas: list[str]
    evidence_notes: list[str]


class GitHubRepositoryHighlightOutput(StrictSchema):
    repository_name: str
    url: str | None
    evidence_level: GitHubEvidenceLevel
    why_it_matters: str
    demonstrated_skills: list[str]
    resume_bullet_suggestion: str
    improvement_note: str


class GitHubRepositoryIssueOutput(StrictSchema):
    repository_name: str
    issue: str
    impact: str
    suggested_fix: str
    priority: GitHubPriority


class GitHubReadmeImprovementOutput(StrictSchema):
    repository_name: str
    current_problem: str
    recommended_sections: list[str]
    example_summary: str


class GitHubCareerAlignmentOutput(StrictSchema):
    role_or_field: str
    alignment_level: GitHubEvidenceLevel
    supporting_repositories: list[str]
    missing_evidence: list[str]
    next_project_idea: str


class GitHubActionOutput(StrictSchema):
    title: str
    priority: GitHubPriority
    reason: str
    steps: list[str]


class LlmGitHubProfileAnalysisOutput(StrictSchema):
    portfolio_score: float = Field(ge=0.0, le=100.0)
    headline: str
    summary: str
    technology_summary: GitHubTechnologySummaryOutput
    strong_repositories: list[GitHubRepositoryHighlightOutput]
    resume_worthy_projects: list[GitHubRepositoryHighlightOutput]
    weak_repositories: list[GitHubRepositoryIssueOutput]
    readme_improvements: list[GitHubReadmeImprovementOutput]
    career_alignment: list[GitHubCareerAlignmentOutput]
    recommended_actions: list[GitHubActionOutput]
    profile_presentation_issues: list[str]


class FallbackGitHubTechnologySummaryOutput(StrictSchema):
    top_languages: list[str]
    tools_and_frameworks: list[str]
    skill_areas: list[str]


class FallbackGitHubRepositoryReviewOutput(StrictSchema):
    repository_name: str
    url: str | None
    resume_usefulness: GitHubEvidenceLevel
    strengths: list[str]
    weaknesses: list[str]
    demonstrated_skills: list[str]
    suggested_resume_bullet: str
    improvement_actions: list[str]


class FallbackGitHubCareerAlignmentOutput(StrictSchema):
    role_or_field: str
    alignment_level: GitHubEvidenceLevel
    supporting_repositories: list[str]
    gaps: list[str]
    next_step: str


class LlmGitHubProfileAnalysisFallbackOutput(StrictSchema):
    portfolio_score: float = Field(ge=0.0, le=100.0)
    headline: str
    summary: str
    technology_summary: FallbackGitHubTechnologySummaryOutput
    repository_reviews: list[FallbackGitHubRepositoryReviewOutput]
    readme_improvements: list[str]
    career_alignment: list[FallbackGitHubCareerAlignmentOutput]
    recommended_actions: list[GitHubActionOutput]
    profile_presentation_issues: list[str]
