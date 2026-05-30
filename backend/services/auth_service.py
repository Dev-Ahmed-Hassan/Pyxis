import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.user import StudentProfile, User
from schemas.auth import SignupRequest
from utils.security import hash_password, verify_password


def get_user_by_email(database: Session, email: str) -> User | None:
    statement = select(User).where(
        func.lower(User.email) == email.lower(),
        User.deleted_at.is_(None),
    )
    return database.scalar(statement)


def get_active_user_by_id(database: Session, user_id: str) -> User | None:
    try:
        parsed_user_id = uuid.UUID(user_id)
    except ValueError:
        return None

    statement = select(User).where(
        User.id == parsed_user_id,
        User.is_active.is_(True),
        User.deleted_at.is_(None),
    )
    return database.scalar(statement)


def create_student(database: Session, signup: SignupRequest) -> User:
    user = User(
        full_name=signup.full_name.strip(),
        email=str(signup.email).lower(),
        password_hash=hash_password(signup.password),
    )
    user.profile = StudentProfile()

    database.add(user)
    database.commit()
    database.refresh(user)
    return user


def authenticate_user(database: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(database, email)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
