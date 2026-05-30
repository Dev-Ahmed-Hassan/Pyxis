from sqlalchemy.orm import Session

from models.user import StudentProfile, User
from schemas.profile import ProfileUpdate


def get_student_profile(database: Session, user: User) -> StudentProfile:
    profile = database.get(StudentProfile, user.id)
    if profile:
        return profile

    profile = StudentProfile(user_id=user.id)
    database.add(profile)
    database.commit()
    database.refresh(profile)
    return profile


def update_student_profile(
    database: Session,
    user: User,
    profile_update: ProfileUpdate,
) -> StudentProfile:
    profile = get_student_profile(database, user)
    changes = profile_update.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(profile, field, value)

    database.commit()
    database.refresh(profile)
    return profile
