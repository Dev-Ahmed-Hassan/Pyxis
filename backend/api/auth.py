from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database.postgres import get_db
from models.user import User
from schemas.auth import LoginRequest, SignupRequest, TokenResponse, UserResponse
from services.auth_service import (
    authenticate_user,
    create_student,
    get_active_user_by_id,
    get_user_by_email,
)
from utils.security import create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["authentication"])
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    database: Session = Depends(get_db),
) -> User:
    try:
        user_id = decode_access_token(credentials.credentials)
    except (RuntimeError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error

    user = get_active_user_by_id(database, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive or no longer exists",
        )
    return user


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(signup_request: SignupRequest, database: Session = Depends(get_db)):
    if get_user_by_email(database, str(signup_request.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    try:
        return create_student(database, signup_request)
    except IntegrityError as error:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        ) from error


@router.post("/login", response_model=TokenResponse)
def login(login_request: LoginRequest, database: Session = Depends(get_db)):
    user = authenticate_user(database, str(login_request.email), login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
