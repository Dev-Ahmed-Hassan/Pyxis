import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    headline: str | None
    bio: str | None
    target_roles: list[str]


class ProfileUpdate(BaseModel):
    headline: str | None = Field(default=None, max_length=160)
    bio: str | None = Field(default=None, max_length=1000)
    target_roles: list[str] | None = Field(default=None, max_length=10)


ProfileSkillSourceSection = Literal["skills_list", "project", "experience", "certification"]
ProfileSkillExtractionSource = Literal["explicit", "inferred", "manual"]
ProfileSkillStrength = Literal["strong", "moderate", "emerging"]


class UserProfileSkillSourceResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    skill_name: str
    canonical_name: str
    source_section: ProfileSkillSourceSection
    source_key: str
    extraction_source: ProfileSkillExtractionSource
    confidence: float
    evidence: str | None
    context: str | None
    created_at: datetime


class UserProfileProjectSourceResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    source_key: str
    project_name: str | None
    description: list[str]
    skills: list[str]
    confidence: float
    evidence: str | None
    created_at: datetime


class UserProfileCertificationSourceResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    source_key: str
    certification_name: str
    issuer: str | None
    date: str | None
    confidence: float
    evidence: str | None
    created_at: datetime


class UserProfileSkillInventoryItem(BaseModel):
    canonical_name: str
    display_name: str
    strength: ProfileSkillStrength
    source_count: int
    resume_ids: list[uuid.UUID]
    source_sections: list[ProfileSkillSourceSection]
    best_confidence: float
    best_evidence: str | None


class UserProfileFactsResponse(BaseModel):
    user_id: uuid.UUID
    skill_inventory: list[UserProfileSkillInventoryItem]
    skill_sources: list[UserProfileSkillSourceResponse]
    project_sources: list[UserProfileProjectSourceResponse]
    certification_sources: list[UserProfileCertificationSourceResponse]


class UserProfileFactsRefreshResponse(UserProfileFactsResponse):
    refreshed_resume_count: int
    skill_source_count: int
    project_source_count: int
    certification_source_count: int
