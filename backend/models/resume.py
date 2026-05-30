import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from models.base import Base


class ResumeProcessingStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    EXTRACTING_TEXT = "extracting_text"
    TEXT_EXTRACTED = "text_extracted"
    PARSING = "parsing"
    VALIDATING = "validating"
    EMBEDDING = "embedding"
    READY = "ready"
    FAILED = "failed"


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    alias: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_path: Mapped[str | None] = mapped_column(Text)
    mongo_document_id: Mapped[str | None] = mapped_column(Text)
    processing_status: Mapped[ResumeProcessingStatus] = mapped_column(
        Enum(
            ResumeProcessingStatus,
            name="resume_processing_status",
            values_callable=lambda statuses: [status.value for status in statuses],
        ),
        nullable=False,
        default=ResumeProcessingStatus.UPLOADED,
    )
    parser_version: Mapped[str | None] = mapped_column(Text)
    processing_error: Mapped[str | None] = mapped_column(Text)
    processing_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processing_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
