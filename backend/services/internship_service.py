import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.internship import InternshipInput, InternshipProcessingStatus
from models.user import User
from schemas.internship import InternshipCreate
from services.analysis_staleness_service import mark_internship_analyses_stale


def list_internship_inputs(database: Session, user: User) -> list[InternshipInput]:
    statement = (
        select(InternshipInput)
        .where(
            InternshipInput.user_id == user.id,
            InternshipInput.deleted_at.is_(None),
        )
        .order_by(InternshipInput.created_at.desc())
    )
    return list(database.scalars(statement))


def get_internship_input(
    database: Session,
    user: User,
    internship_id: uuid.UUID,
) -> InternshipInput:
    return _get_owned_internship_input(database, user, internship_id)


def create_internship_input(
    database: Session,
    user: User,
    internship_create: InternshipCreate,
) -> InternshipInput:
    internship = InternshipInput(
        user_id=user.id,
        label=internship_create.label.strip(),
        original_description=internship_create.original_description.strip(),
        application_url=(
            str(internship_create.application_url)
            if internship_create.application_url
            else None
        ),
    )
    database.add(internship)
    database.commit()
    database.refresh(internship)
    return internship


def retry_internship_processing(
    database: Session,
    user: User,
    internship_id: uuid.UUID,
) -> InternshipInput:
    internship = _get_owned_internship_input(database, user, internship_id)
    if internship.processing_status != InternshipProcessingStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only failed internship inputs can be retried",
        )

    return _reset_internship_processing(database, internship)


def reparse_internship_requirements(
    database: Session,
    user: User,
    internship_id: uuid.UUID,
) -> InternshipInput:
    internship = _get_owned_internship_input(database, user, internship_id)
    if internship.processing_status in {
        InternshipProcessingStatus.SUBMITTED,
        InternshipProcessingStatus.PARSING,
        InternshipProcessingStatus.VALIDATING,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Internship parsing is already queued or in progress",
        )

    return _reset_internship_processing(database, internship)


def soft_delete_internship_input(
    database: Session,
    user: User,
    internship_id: uuid.UUID,
) -> None:
    internship = _get_owned_internship_input(database, user, internship_id)
    internship.deleted_at = datetime.now(UTC)
    mark_internship_analyses_stale(
        database,
        internship.id,
        stale_at=internship.deleted_at,
    )
    database.commit()


def _get_owned_internship_input(
    database: Session,
    user: User,
    internship_id: uuid.UUID,
) -> InternshipInput:
    statement = select(InternshipInput).where(
        InternshipInput.id == internship_id,
        InternshipInput.user_id == user.id,
        InternshipInput.deleted_at.is_(None),
    )
    internship = database.scalar(statement)
    if not internship:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Internship input not found",
        )
    return internship


def _reset_internship_processing(
    database: Session,
    internship: InternshipInput,
) -> InternshipInput:
    internship.processing_status = InternshipProcessingStatus.SUBMITTED
    internship.processing_error = None
    internship.processing_attempts = 0
    internship.processing_started_at = None
    internship.processing_completed_at = None
    internship.next_retry_at = None
    mark_internship_analyses_stale(database, internship.id)
    database.commit()
    database.refresh(internship)
    return internship
