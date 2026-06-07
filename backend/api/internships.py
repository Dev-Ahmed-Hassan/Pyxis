import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from api.auth import get_current_user
from database.postgres import get_db
from models.user import User
from schemas.internship import InternshipCreate, InternshipResponse, ParsedInternshipResponse
from services.internship_profile_service import get_parsed_internship_requirements
from services.internship_service import (
    create_internship_input,
    get_internship_input,
    list_internship_inputs,
    reparse_internship_requirements,
    retry_internship_processing,
    soft_delete_internship_input,
)

router = APIRouter(prefix="/internships", tags=["internships"])


@router.get("", response_model=list[InternshipResponse])
def get_internships(
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return list_internship_inputs(database, current_user)


@router.post("", response_model=InternshipResponse, status_code=status.HTTP_201_CREATED)
def create_internship(
    internship_create: InternshipCreate,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return create_internship_input(database, current_user, internship_create)


@router.get("/{internship_id}", response_model=InternshipResponse)
def get_internship(
    internship_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_internship_input(database, current_user, internship_id)


@router.post("/{internship_id}/retry", response_model=InternshipResponse)
def retry_internship(
    internship_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return retry_internship_processing(database, current_user, internship_id)


@router.post("/{internship_id}/reparse", response_model=InternshipResponse)
def reparse_internship(
    internship_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return reparse_internship_requirements(database, current_user, internship_id)


@router.get("/{internship_id}/parsed-requirements", response_model=ParsedInternshipResponse)
def get_parsed_requirements(
    internship_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_parsed_internship_requirements(database, current_user, internship_id)


@router.delete("/{internship_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_internship(
    internship_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    soft_delete_internship_input(database, current_user, internship_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
