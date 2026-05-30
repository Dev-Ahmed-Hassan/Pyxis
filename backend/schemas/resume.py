import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.resume import ResumeProcessingStatus


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    alias: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    processing_status: ResumeProcessingStatus
    processing_error: str | None
    processing_attempts: int
    processing_started_at: datetime | None
    processing_completed_at: datetime | None
    next_retry_at: datetime | None
    is_default: bool
    created_at: datetime
    updated_at: datetime


class ResumeUpdate(BaseModel):
    alias: str | None = Field(default=None, min_length=1, max_length=80)
    is_default: bool | None = None
