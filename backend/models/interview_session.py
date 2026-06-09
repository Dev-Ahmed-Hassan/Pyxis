import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from models.base import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    match_analysis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("match_analyses.id", ondelete="CASCADE"), nullable=False)
    match_explanation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("match_explanations.id", ondelete="SET NULL"))
    github_evidence_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("github_match_evidence.id", ondelete="SET NULL"))

    # status: created | in_progress | completed | abandoned
    status: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(Text, nullable=False)
    question_target: Mapped[int] = mapped_column(Integer, nullable=False)
    focus_areas: Mapped[dict] = mapped_column(JSONB, nullable=False)

    compact_context: Mapped[dict] = mapped_column(JSONB, nullable=False)
    interview_plan: Mapped[dict] = mapped_column(JSONB, nullable=False)
    rolling_summary: Mapped[str | None] = mapped_column(Text)
    current_question_number: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    session_version: Mapped[int] = mapped_column(Integer, nullable=False)
    prompt_version: Mapped[int] = mapped_column(Integer, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stale_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    questions: Mapped[list["InterviewQuestion"]] = relationship(
        "InterviewQuestion", back_populates="session", cascade="all, delete-orphan"
    )
    answers: Mapped[list["InterviewAnswer"]] = relationship(
        "InterviewAnswer", back_populates="session", cascade="all, delete-orphan"
    )
    evaluation: Mapped["InterviewEvaluation | None"] = relationship(
        "InterviewEvaluation", back_populates="session", uselist=False, cascade="all, delete-orphan"
    )
