import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from models.base import Base


class SemanticEmbeddingRefreshStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    RETRYING = "retrying"
    COMPLETE = "complete"
    FAILED = "failed"


class SemanticEmbeddingRefreshJob(Base):
    __tablename__ = "semantic_embedding_refresh_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
    )
    internship_input_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("internship_inputs.id", ondelete="CASCADE"),
    )
    generation: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        default=uuid.uuid4,
    )
    status: Mapped[SemanticEmbeddingRefreshStatus] = mapped_column(
        Enum(
            SemanticEmbeddingRefreshStatus,
            name="semantic_embedding_refresh_status",
            values_callable=lambda statuses: [status.value for status in statuses],
        ),
        nullable=False,
        default=SemanticEmbeddingRefreshStatus.QUEUED,
    )
    processing_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processing_error: Mapped[str | None] = mapped_column(Text)
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processing_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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
