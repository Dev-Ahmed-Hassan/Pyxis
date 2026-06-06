from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from services.ai.schemas import (
    Certification,
    Education,
    Experience,
    ExtractedSkill,
    ExtractedText,
    ParsedResume,
    Project,
)
from services.skill_canonicalizer import canonicalize_parsed_resume


class StudentProfileSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ManualExperience(StudentProfileSchema):
    company: str | None = Field(default=None, max_length=160)
    role: str | None = Field(default=None, max_length=160)
    start_date: str | None = Field(default=None, max_length=40)
    end_date: str | None = Field(default=None, max_length=40)
    description: list[str] = Field(default_factory=list, max_length=20)
    skills: list[str] = Field(default_factory=list, max_length=50)


class ManualProject(StudentProfileSchema):
    name: str | None = Field(default=None, max_length=160)
    description: list[str] = Field(default_factory=list, max_length=20)
    skills: list[str] = Field(default_factory=list, max_length=50)


class ManualEducation(StudentProfileSchema):
    institution: str | None = Field(default=None, max_length=200)
    degree: str | None = Field(default=None, max_length=160)
    field_of_study: str | None = Field(default=None, max_length=160)
    start_date: str | None = Field(default=None, max_length=40)
    end_date: str | None = Field(default=None, max_length=40)


class ManualCertification(StudentProfileSchema):
    name: str = Field(max_length=200)
    issuer: str | None = Field(default=None, max_length=200)
    date: str | None = Field(default=None, max_length=40)


class ParsedResumeUpdate(StudentProfileSchema):
    full_name: str | None = Field(default=None, max_length=160)
    email: str | None = Field(default=None, max_length=320)
    phone: str | None = Field(default=None, max_length=80)
    location: str | None = Field(default=None, max_length=200)
    summary: str | None = Field(default=None, max_length=2000)
    skills: list[str] | None = Field(default=None, max_length=100)
    experience: list[ManualExperience] | None = Field(default=None, max_length=30)
    projects: list[ManualProject] | None = Field(default=None, max_length=30)
    education: list[ManualEducation] | None = Field(default=None, max_length=20)
    certifications: list[ManualCertification] | None = Field(default=None, max_length=30)


class ParsedResumeResponse(StudentProfileSchema):
    parsed_resume: ParsedResume
    field_provenance: dict[str, str]
    updated_at: datetime


def apply_manual_updates(parsed_resume: ParsedResume, changes: dict) -> ParsedResume:
    updated = parsed_resume.model_dump()
    for field, value in changes.items():
        if field in {"full_name", "email", "phone", "location", "summary"}:
            updated[field] = _manual_text(value).model_dump()
        elif field == "skills":
            updated[field] = [_manual_skill(skill).model_dump() for skill in value]
        elif field == "experience":
            updated[field] = [_manual_experience(item).model_dump() for item in value]
        elif field == "projects":
            updated[field] = [_manual_project(item).model_dump() for item in value]
        elif field == "education":
            updated[field] = [_manual_education(item).model_dump() for item in value]
        elif field == "certifications":
            updated[field] = [_manual_certification(item).model_dump() for item in value]
    return canonicalize_parsed_resume(ParsedResume.model_validate(updated))


def _manual_text(value: str | None) -> ExtractedText:
    return ExtractedText(value=value, confidence=1.0, evidence=None)


def _manual_skill(value: str) -> ExtractedSkill:
    return ExtractedSkill(name=value, confidence=1.0, evidence=None, source="manual")


def _manual_experience(value: ManualExperience | dict) -> Experience:
    data = ManualExperience.model_validate(value).model_dump()
    data["skills"] = [_manual_skill(skill) for skill in data["skills"]]
    return Experience(**data, confidence=1.0, evidence=None)


def _manual_project(value: ManualProject | dict) -> Project:
    data = ManualProject.model_validate(value).model_dump()
    data["skills"] = [_manual_skill(skill) for skill in data["skills"]]
    return Project(**data, confidence=1.0, evidence=None)


def _manual_education(value: ManualEducation | dict) -> Education:
    data = ManualEducation.model_validate(value).model_dump()
    return Education(**data, confidence=1.0, evidence=None)


def _manual_certification(value: ManualCertification | dict) -> Certification:
    data = ManualCertification.model_validate(value).model_dump()
    return Certification(**data, confidence=1.0, evidence=None)
