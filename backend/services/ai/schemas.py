from pydantic import BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExtractedText(StrictSchema):
    value: str | None
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str | None


class ExtractedSkill(StrictSchema):
    name: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str | None


class Experience(StrictSchema):
    company: str | None
    role: str | None
    start_date: str | None
    end_date: str | None
    description: list[str]
    skills: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str | None


class Project(StrictSchema):
    name: str | None
    description: list[str]
    skills: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str | None


class Education(StrictSchema):
    institution: str | None
    degree: str | None
    field_of_study: str | None
    start_date: str | None
    end_date: str | None
    confidence: float = Field(ge=0.0, le=1.0)
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
