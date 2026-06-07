import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class GitHubSnapshotCreate(BaseModel):
    github_username: str = Field(min_length=1, max_length=80)
    repository_limit: int = Field(default=12, ge=1, le=25)


class GitHubProfileSnapshotResponse(BaseModel):
    id: uuid.UUID
    github_username: str
    profile_payload: dict
    repositories_payload: list[dict]
    languages_payload: dict[str, dict]
    readmes_payload: dict[str, dict | None]
    compact_snapshot: dict
    repository_limit: int
    fetched_at: datetime
    created_at: datetime


class GitHubCompactSnapshotResponse(BaseModel):
    id: uuid.UUID
    github_username: str
    compact_snapshot: dict
    repository_limit: int
    fetched_at: datetime
    created_at: datetime


class GitHubProfileAnalysisCreate(BaseModel):
    snapshot_id: uuid.UUID | None = None
    target_field: str | None = Field(default=None, max_length=120)
    preferred_roles: list[str] = Field(default_factory=list, max_length=8)
    force_refresh: bool = False


class GitHubTechnologySummary(BaseModel):
    top_languages: list[str]
    detected_frameworks_or_tools: list[str]
    likely_skill_areas: list[str]
    evidence_notes: list[str]


class GitHubRepositoryHighlight(BaseModel):
    repository_name: str
    url: str | None
    evidence_level: str
    why_it_matters: str
    demonstrated_skills: list[str]
    resume_bullet_suggestion: str
    improvement_note: str


class GitHubRepositoryIssue(BaseModel):
    repository_name: str
    issue: str
    impact: str
    suggested_fix: str
    priority: str


class GitHubReadmeImprovement(BaseModel):
    repository_name: str
    current_problem: str
    recommended_sections: list[str]
    example_summary: str


class GitHubCareerAlignment(BaseModel):
    role_or_field: str
    alignment_level: str
    supporting_repositories: list[str]
    missing_evidence: list[str]
    next_project_idea: str


class GitHubAction(BaseModel):
    title: str
    priority: str
    reason: str
    steps: list[str]


class GitHubProfileAnalysisPayload(BaseModel):
    portfolio_score: float
    headline: str
    summary: str
    technology_summary: GitHubTechnologySummary
    strong_repositories: list[GitHubRepositoryHighlight]
    resume_worthy_projects: list[GitHubRepositoryHighlight]
    weak_repositories: list[GitHubRepositoryIssue]
    readme_improvements: list[GitHubReadmeImprovement]
    career_alignment: list[GitHubCareerAlignment]
    recommended_actions: list[GitHubAction]
    profile_presentation_issues: list[str]


class GitHubProfileAnalysisResponse(BaseModel):
    id: uuid.UUID
    snapshot_id: uuid.UUID
    github_username: str
    analysis_version: str
    prompt_version: str
    provider: str
    model_name: str
    analysis_request: dict
    compact_snapshot_used: dict
    analysis: GitHubProfileAnalysisPayload
    created_at: datetime
    stale_at: datetime | None
