from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExtractedText(StrictSchema):
    value: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str | None


class ExtractedSkill(StrictSchema):
    name: str
    canonical_name: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str | None
    source: Literal["explicit", "inferred", "manual"] = "explicit"


class Experience(StrictSchema):
    company: str | None
    role: str | None
    start_date: str | None
    end_date: str | None
    description: list[str]
    skills: list[ExtractedSkill]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str | None

    @field_validator("skills", mode="before")
    @classmethod
    def accept_legacy_skill_names(cls, skills: list) -> list:
        return [_legacy_skill(skill) for skill in skills]


class Project(StrictSchema):
    name: str | None
    description: list[str]
    skills: list[ExtractedSkill]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str | None

    @field_validator("skills", mode="before")
    @classmethod
    def accept_legacy_skill_names(cls, skills: list) -> list:
        return [_legacy_skill(skill) for skill in skills]


class Education(StrictSchema):
    institution: str | None
    degree: str | None
    field_of_study: str | None
    start_date: str | None
    end_date: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str | None


class Certification(StrictSchema):
    name: str
    issuer: str | None = None
    date: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str | None


class ReviewWarning(StrictSchema):
    field: str
    message: str
    evidence: str | None


class ParsedResume(StrictSchema):
    full_name: ExtractedText
    email: ExtractedText
    phone: ExtractedText
    location: ExtractedText
    summary: ExtractedText
    skills: list[ExtractedSkill]
    experience: list[Experience]
    projects: list[Project]
    education: list[Education]
    certifications: list[Certification] = Field(default_factory=list)
    review_warnings: list[ReviewWarning] = Field(default_factory=list)


def _legacy_skill(skill: str | dict) -> str | dict:
    if isinstance(skill, str):
        return {
            "name": skill,
            "confidence": 1.0,
            "evidence": None,
            "source": "explicit",
        }
    return skill
