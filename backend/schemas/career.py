import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from schemas.matching import MatchExplainabilityKnowledgeChunkResponse

CareerFitLevel = Literal["strong", "good", "emerging", "explore_later"]
CareerPriority = Literal["high", "medium", "low"]


class CareerRecommendationCreate(BaseModel):
    target_field: str | None = Field(default=None, max_length=120)
    preferred_roles: list[str] = Field(default_factory=list, max_length=8)


class CareerPathRecommendation(BaseModel):
    path: str
    fit_level: CareerFitLevel
    fit_score: float
    why_it_fits: str
    supporting_skills: list[str]
    supporting_projects: list[str]
    supporting_certifications: list[str]
    missing_skills: list[str]
    next_steps: list[str]
    internship_titles_to_search: list[str]


class CareerSkillGap(BaseModel):
    skill: str
    priority: CareerPriority
    related_paths: list[str]
    why_it_matters: str
    suggested_action: str


class CareerProjectRecommendation(BaseModel):
    title: str
    target_paths: list[str]
    goal: str
    tools: list[str]
    steps: list[str]
    resume_outcome: str


class CareerRoadmapStep(BaseModel):
    order: int
    title: str
    focus: str
    actions: list[str]
    expected_outcome: str


class CareerRecommendationPayload(BaseModel):
    headline: str
    summary: str
    primary_paths: list[CareerPathRecommendation]
    secondary_paths: list[CareerPathRecommendation]
    paths_to_delay: list[CareerPathRecommendation]
    profile_strengths: list[str]
    skill_gaps: list[CareerSkillGap]
    recommended_projects: list[CareerProjectRecommendation]
    learning_roadmap: list[CareerRoadmapStep]
    internship_search_terms: list[str]


class CareerRecommendationResponse(BaseModel):
    id: uuid.UUID
    recommendation_version: str
    prompt_version: str
    provider: str
    model_name: str
    target_field: str | None
    preferred_roles: list[str]
    profile_snapshot: dict
    retrieved_knowledge_chunks: list[MatchExplainabilityKnowledgeChunkResponse]
    recommendation: CareerRecommendationPayload
    created_at: datetime
    stale_at: datetime | None


class GraphCareerLearningStep(BaseModel):
    order: int
    skill: str
    already_known: bool


class GraphCareerSkillGap(BaseModel):
    skill: str
    importance: Literal["required", "preferred"]
    path_from_skill: str | None
    learning_steps: list[GraphCareerLearningStep]


class GraphCareerRelatedSupport(BaseModel):
    requirement: str
    supporting_skill: str
    support_path: list[str]
    credit_factor: float


class GraphCareerPath(BaseModel):
    role: str
    description: str
    domain: str
    fit_score: float
    fit_level: CareerFitLevel
    exact_required_coverage: float
    matched_skills: list[str]
    related_skill_support: list[GraphCareerRelatedSupport]
    missing_required_skills: list[str]
    missing_preferred_skills: list[str]
    learning_gaps: list[GraphCareerSkillGap]


class GraphCareerRecommendationsResponse(BaseModel):
    version: str
    user_id: uuid.UUID
    profile_skill_count: int
    graph_source: Literal["neo4j", "local_dataset"]
    recommendations: list[GraphCareerPath]
    warnings: list[str]
