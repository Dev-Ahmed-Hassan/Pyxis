from typing import Literal

from pydantic import Field

from services.ai.schemas import StrictSchema

CareerFitLevel = Literal["strong", "good", "emerging", "explore_later"]
CareerPriority = Literal["high", "medium", "low"]


class CareerPathRecommendationOutput(StrictSchema):
    path: str
    fit_level: CareerFitLevel
    fit_score: float = Field(ge=0.0, le=100.0)
    why_it_fits: str
    supporting_skills: list[str]
    supporting_projects: list[str]
    supporting_certifications: list[str]
    missing_skills: list[str]
    next_steps: list[str]
    internship_titles_to_search: list[str]


class CareerSkillGapOutput(StrictSchema):
    skill: str
    priority: CareerPriority
    related_paths: list[str]
    why_it_matters: str
    suggested_action: str


class CareerProjectRecommendationOutput(StrictSchema):
    title: str
    target_paths: list[str]
    goal: str
    tools: list[str]
    steps: list[str]
    resume_outcome: str


class CareerRoadmapStepOutput(StrictSchema):
    order: int
    title: str
    focus: str
    actions: list[str]
    expected_outcome: str


class LlmCareerRecommendationOutput(StrictSchema):
    headline: str
    summary: str
    primary_paths: list[CareerPathRecommendationOutput]
    secondary_paths: list[CareerPathRecommendationOutput]
    paths_to_delay: list[CareerPathRecommendationOutput]
    profile_strengths: list[str]
    skill_gaps: list[CareerSkillGapOutput]
    recommended_projects: list[CareerProjectRecommendationOutput]
    learning_roadmap: list[CareerRoadmapStepOutput]
    internship_search_terms: list[str]
