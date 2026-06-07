import uuid

from fastapi import HTTPException, status
from pymongo.errors import PyMongoError
from sqlalchemy.orm import Session

from database.mongodb import get_mongodb_database
from models.internship import InternshipProcessingStatus
from models.user import User
from schemas.internship import ParsedInternshipResponse
from services.ai.internship_schemas import ParsedInternship
from services.internship_service import get_internship_input


def get_parsed_internship_requirements(
    database: Session,
    user: User,
    internship_id: uuid.UUID,
) -> ParsedInternshipResponse:
    internship = get_internship_input(database, user, internship_id)
    if internship.processing_status != InternshipProcessingStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Internship parsing is not ready",
        )

    try:
        document = get_mongodb_database().internship_inputs.find_one(
            {"postgres_internship_id": str(internship.id)},
            {
                "parsed_internship": 1,
                "updated_at": 1,
            },
        )
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Parsed internship storage is temporarily unavailable",
        ) from error

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parsed internship document not found",
        )

    try:
        return ParsedInternshipResponse(
            parsed_internship=ParsedInternship.model_validate(document["parsed_internship"]),
            updated_at=document["updated_at"],
        )
    except (KeyError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored parsed internship is missing or invalid",
        ) from error
