import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from models.base import Base


class GitHubProfileSnapshot(Base):
    __tablename__ = "github_profile_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    github_username: Mapped[str] = mapped_column(Text, nullable=False)
    profile_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    repositories_payload: Mapped[list] = mapped_column(JSONB, nullable=False)
    languages_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    readmes_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    compact_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    repository_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
