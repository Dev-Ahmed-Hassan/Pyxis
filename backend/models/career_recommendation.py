import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from models.base import Base


class CareerRecommendation(Base):
    __tablename__ = "career_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recommendation_version: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_version: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    target_field: Mapped[str | None] = mapped_column(Text)
    preferred_roles: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False)
    profile_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    retrieved_knowledge_chunks: Mapped[list] = mapped_column(JSONB, nullable=False)
    recommendation_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    stale_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
