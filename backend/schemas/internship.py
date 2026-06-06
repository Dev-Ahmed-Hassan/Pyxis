import uuid
from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field

from models.internship import InternshipProcessingStatus
from services.ai.internship_schemas import ParsedInternship


class InternshipCreate(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    original_description: str = Field(min_length=50, max_length=20000)
    application_url: AnyHttpUrl | None = None


class InternshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    application_url: str | None
    processing_status: InternshipProcessingStatus
    processing_error: str | None
    processing_attempts: int
    processing_started_at: datetime | None
    processing_completed_at: datetime | None
    next_retry_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ParsedInternshipResponse(BaseModel):
    parsed_internship: ParsedInternship
    updated_at: datetime
