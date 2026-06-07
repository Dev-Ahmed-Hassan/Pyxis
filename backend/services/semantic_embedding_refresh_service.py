import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from models.user import User
from schemas.matching import SemanticEmbeddingRefreshResponse
from services.ai.config import AIConfigurationError, get_embedding_route
from services.ai.providers.base import AIProviderError
from services.analysis_staleness_service import (
    mark_internship_analyses_stale,
    mark_resume_analyses_stale,
)
from services.internship_profile_service import get_parsed_internship_requirements
from services.resume_profile_service import get_parsed_resume_profile
from services.semantic_embedding_service import (
    refresh_internship_requirement_embeddings,
    refresh_resume_section_embeddings,
)


def refresh_match_embeddings(
    database: Session,
    user: User,
    resume_id: uuid.UUID,
    internship_id: uuid.UUID,
) -> SemanticEmbeddingRefreshResponse:
    try:
        route = get_embedding_route()
    except AIConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
    if not route:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Semantic embeddings are not configured",
        )

    resume = get_parsed_resume_profile(database, user, resume_id)
    internship = get_parsed_internship_requirements(database, user, internship_id)
    try:
        resume_count = refresh_resume_section_embeddings(
            database,
            resume_id,
            resume.parsed_resume,
        )
        requirement_count = refresh_internship_requirement_embeddings(
            database,
            internship_id,
            internship.parsed_internship,
        )
    except AIConfigurationError as error:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error
    except AIProviderError as error:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except SQLAlchemyError as error:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Semantic embedding storage is unavailable. "
                "Apply migration 007_semantic_embeddings.sql."
            ),
        ) from error

    mark_resume_analyses_stale(database, resume_id)
    mark_internship_analyses_stale(database, internship_id)
    database.commit()
    return SemanticEmbeddingRefreshResponse(
        resume_id=resume_id,
        internship_id=internship_id,
        model_name=route.model,
        resume_section_embedding_count=resume_count,
        internship_requirement_embedding_count=requirement_count,
    )
