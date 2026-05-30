from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.auth import get_current_user
from database.postgres import get_db
from models.user import User
from schemas.profile import ProfileResponse, ProfileUpdate
from services.profile_service import get_student_profile, update_student_profile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_student_profile(database, current_user)


@router.patch("", response_model=ProfileResponse)
def update_profile(
    profile_update: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return update_student_profile(database, current_user, profile_update)
