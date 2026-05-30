import uuid

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlalchemy.orm import Session

from api.auth import get_current_user
from database.postgres import get_db
from models.user import User
from schemas.resume import ResumeResponse, ResumeUpdate
from schemas.resume_profile import ParsedResumeResponse, ParsedResumeUpdate
from services.resume_profile_service import get_parsed_resume_profile, update_parsed_resume_profile
from services.resume_service import (
    create_resume,
    get_resume,
    list_resumes,
    retry_resume_processing,
    soft_delete_resume,
    update_resume,
)

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.get("", response_model=list[ResumeResponse])
def get_resumes(
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return list_resumes(database, current_user)


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
def upload_resume(
    alias: str = Form(min_length=1, max_length=80),
    uploaded_file: UploadFile = File(),
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return create_resume(database, current_user, alias, uploaded_file)


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume_status(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_resume(database, current_user, resume_id)


@router.patch("/{resume_id}", response_model=ResumeResponse)
def patch_resume(
    resume_id: uuid.UUID,
    resume_update: ResumeUpdate,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return update_resume(database, current_user, resume_id, resume_update)


@router.post("/{resume_id}/retry", response_model=ResumeResponse)
def retry_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return retry_resume_processing(database, current_user, resume_id)


@router.get("/{resume_id}/parsed-profile", response_model=ParsedResumeResponse)
def get_parsed_profile(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_parsed_resume_profile(database, current_user, resume_id)


@router.patch("/{resume_id}/parsed-profile", response_model=ParsedResumeResponse)
def patch_parsed_profile(
    resume_id: uuid.UUID,
    profile_update: ParsedResumeUpdate,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return update_parsed_resume_profile(database, current_user, resume_id, profile_update)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    soft_delete_resume(database, current_user, resume_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
