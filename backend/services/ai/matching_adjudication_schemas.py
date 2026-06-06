from typing import Literal

from pydantic import Field

from services.ai.schemas import StrictSchema


class LlmRequirementJudgmentOutput(StrictSchema):
    requirement: str
    requirement_category: Literal["required_skill", "preferred_skill"]
    support_level: Literal["direct", "strong_partial", "weak_related", "absent"]
    confidence: float = Field(ge=0.0, le=1.0)
    cited_resume_section_keys: list[str]
    reason: str


class LlmFairnessAuditOutput(StrictSchema):
    assessment: Literal[
        "fair",
        "potentially_underestimated",
        "potentially_overestimated",
        "needs_manual_review",
    ]
    reason: str
    review_requirements: list[str]


class LlmMatchAdjudicationOutput(StrictSchema):
    requirement_judgments: list[LlmRequirementJudgmentOutput]
    fairness_audit: LlmFairnessAuditOutput
