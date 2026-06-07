import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from pymongo.errors import PyMongoError
from sqlalchemy.orm import Session

from database.mongodb import get_mongodb_database
from models.resume import ResumeProcessingStatus
from models.user import User
from schemas.resume_profile import (
    ParsedResumeResponse,
    ParsedResumeUpdate,
    apply_manual_updates,
)
from services.ai.schemas import ParsedResume
from services.analysis_staleness_service import mark_resume_analyses_stale
from services.resume_parsing_service import PARSED_RESUME_FIELDS
from services.resume_service import get_resume
from services.semantic_embedding_service import (
    invalidate_resume_section_embeddings,
)
from services.semantic_embedding_queue_service import enqueue_resume_embedding_refresh
from services.user_profile_facts_service import replace_profile_facts_for_resume


def get_parsed_resume_profile(
    database: Session,
    user: User,
    resume_id: uuid.UUID,
) -> ParsedResumeResponse:
    resume = get_resume(database, user, resume_id)
    if resume.processing_status != ResumeProcessingStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resume parsing is not ready",
        )

    document = _get_resume_document(str(resume.id))
    try:
        parsed_resume = ParsedResume.model_validate(document["parsed_resume"])
    except (KeyError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored parsed resume is missing or invalid",
        ) from error

    try:
        return ParsedResumeResponse(
            parsed_resume=parsed_resume,
            field_provenance=_get_field_provenance(document),
            updated_at=document["updated_at"],
        )
    except KeyError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored parsed resume is missing or invalid",
        ) from error


def update_parsed_resume_profile(
    database: Session,
    user: User,
    resume_id: uuid.UUID,
    profile_update: ParsedResumeUpdate,
) -> ParsedResumeResponse:
    resume = get_resume(database, user, resume_id)
    if resume.processing_status != ResumeProcessingStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resume parsing is not ready",
        )

    document = _get_resume_document(str(resume.id))
    try:
        parsed_resume = ParsedResume.model_validate(document["parsed_resume"])
    except (KeyError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored parsed resume is missing or invalid",
        ) from error

    changes = profile_update.model_dump(exclude_unset=True)
    if not changes:
        return get_parsed_resume_profile(database, user, resume_id)

    updated_resume = apply_manual_updates(parsed_resume, changes)
    now = datetime.now(UTC)
    provenance_updates = {
        f"field_provenance.{field}": "manually_updated" for field in changes
    }
    try:
        get_mongodb_database().resumes.update_one(
            {"postgres_resume_id": str(resume.id)},
            {
                "$set": {
                    "parsed_resume": updated_resume.model_dump(mode="json"),
                    "updated_at": now,
                    **provenance_updates,
                }
            },
        )
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Parsed resume storage is temporarily unavailable",
        ) from error

    invalidate_resume_section_embeddings(database, resume.id)
    replace_profile_facts_for_resume(database, user.id, resume.id, updated_resume)
    mark_resume_analyses_stale(database, resume.id, stale_at=now)
    database.commit()
    enqueue_resume_embedding_refresh(database, resume.id)
    return get_parsed_resume_profile(database, user, resume_id)


def _get_resume_document(resume_id: str) -> dict:
    try:
        document = get_mongodb_database().resumes.find_one(
            {"postgres_resume_id": resume_id},
            {
                "parsed_resume": 1,
                "field_provenance": 1,
                "updated_at": 1,
            },
        )
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Parsed resume storage is temporarily unavailable",
        ) from error

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parsed resume document not found",
        )
    return document


def _get_field_provenance(document: dict) -> dict[str, str]:
    provenance = {field: "extracted" for field in PARSED_RESUME_FIELDS}
    provenance.update(document.get("field_provenance", {}))
    return provenance
