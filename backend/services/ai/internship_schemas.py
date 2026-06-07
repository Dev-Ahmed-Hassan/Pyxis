from pydantic import Field

from services.ai.schemas import ExtractedSkill, ExtractedText, ReviewWarning, StrictSchema


class ParsedInternship(StrictSchema):
    title: ExtractedText
    company: ExtractedText
    location: ExtractedText
    experience_level: ExtractedText
    required_skills: list[ExtractedSkill]
    preferred_skills: list[ExtractedSkill]
    required_domain_concepts: list[ExtractedSkill] = Field(default_factory=list)
    preferred_domain_concepts: list[ExtractedSkill] = Field(default_factory=list)
    required_soft_skills: list[ExtractedSkill] = Field(default_factory=list)
    preferred_soft_skills: list[ExtractedSkill] = Field(default_factory=list)
    responsibilities: list[str]
    qualifications: list[str]
    review_warnings: list[ReviewWarning] = Field(default_factory=list)
