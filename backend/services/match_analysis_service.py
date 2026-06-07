import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.match_analysis import MatchAnalysis
from models.user import User
from schemas.matching import (
    MatchAnalysisCreate,
    MatchAnalysisResponse,
    MatchPreviewResponse,
)
from services.matching_service import get_match_preview


def create_match_analysis(
    database: Session,
    user: User,
    analysis_create: MatchAnalysisCreate,
) -> MatchAnalysisResponse:
    match = get_match_preview(
        database=database,
        user=user,
        resume_id=analysis_create.resume_id,
        internship_id=analysis_create.internship_id,
    )
    analysis = MatchAnalysis(
        user_id=user.id,
        resume_id=analysis_create.resume_id,
        internship_input_id=analysis_create.internship_id,
        analysis_session_id=analysis_create.analysis_session_id or uuid.uuid4(),
        score_version=match.score_version,
        overall_score=match.overall_score,
        analysis_payload=match.model_dump(mode="json"),
    )
    database.add(analysis)
    database.commit()
    database.refresh(analysis)
    return _to_response(analysis)


def list_match_analyses(
    database: Session,
    user: User,
) -> list[MatchAnalysisResponse]:
    statement = (
        select(MatchAnalysis)
        .where(MatchAnalysis.user_id == user.id)
        .order_by(MatchAnalysis.created_at.desc())
    )
    return [_to_response(analysis) for analysis in database.scalars(statement)]


def get_match_analysis(
    database: Session,
    user: User,
    analysis_id: uuid.UUID,
) -> MatchAnalysisResponse:
    return _to_response(_get_owned_match_analysis(database, user, analysis_id))


def _get_owned_match_analysis(
    database: Session,
    user: User,
    analysis_id: uuid.UUID,
) -> MatchAnalysis:
    statement = select(MatchAnalysis).where(
        MatchAnalysis.id == analysis_id,
        MatchAnalysis.user_id == user.id,
    )
    analysis = database.scalar(statement)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match analysis not found",
        )
    return analysis


def _to_response(analysis: MatchAnalysis) -> MatchAnalysisResponse:
    return MatchAnalysisResponse(
        id=analysis.id,
        resume_id=analysis.resume_id,
        internship_input_id=analysis.internship_input_id,
        analysis_session_id=analysis.analysis_session_id,
        score_version=analysis.score_version,
        overall_score=float(analysis.overall_score),
        created_at=analysis.created_at,
        stale_at=analysis.stale_at,
        match=MatchPreviewResponse.model_validate(analysis.analysis_payload),
    )
