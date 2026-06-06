import uuid
from datetime import UTC, datetime

from sqlalchemy import update
from sqlalchemy.orm import Session

from models.match_analysis import MatchAnalysis
from models.match_llm_adjudication import MatchLlmAdjudication


def mark_resume_analyses_stale(
    database: Session,
    resume_id: uuid.UUID,
    stale_at: datetime | None = None,
) -> None:
    database.execute(
        update(MatchAnalysis)
        .where(
            MatchAnalysis.resume_id == resume_id,
            MatchAnalysis.stale_at.is_(None),
        )
        .values(stale_at=stale_at or datetime.now(UTC))
    )
    database.execute(
        update(MatchLlmAdjudication)
        .where(
            MatchLlmAdjudication.resume_id == resume_id,
            MatchLlmAdjudication.stale_at.is_(None),
        )
        .values(stale_at=stale_at or datetime.now(UTC))
    )


def mark_internship_analyses_stale(
    database: Session,
    internship_id: uuid.UUID,
    stale_at: datetime | None = None,
) -> None:
    database.execute(
        update(MatchAnalysis)
        .where(
            MatchAnalysis.internship_input_id == internship_id,
            MatchAnalysis.stale_at.is_(None),
        )
        .values(stale_at=stale_at or datetime.now(UTC))
    )
    database.execute(
        update(MatchLlmAdjudication)
        .where(
            MatchLlmAdjudication.internship_input_id == internship_id,
            MatchLlmAdjudication.stale_at.is_(None),
        )
        .values(stale_at=stale_at or datetime.now(UTC))
    )
