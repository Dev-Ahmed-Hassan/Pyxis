import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.resume import Resume, ResumeProcessingStatus
from models.user import User
from schemas.resume import ResumeUpdate

UPLOAD_DIRECTORY = Path(__file__).resolve().parent.parent / "uploads"
MAX_RESUME_SIZE_BYTES = 10 * 1024 * 1024
MAX_ACTIVE_RESUMES = 5
ALLOWED_FILE_TYPES = {
    ".pdf": {"application/pdf"},
    ".docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/octet-stream",
    },
}


def list_resumes(database: Session, user: User) -> list[Resume]:
    statement = (
        select(Resume)
        .where(
            Resume.user_id == user.id,
            Resume.deleted_at.is_(None),
        )
        .order_by(Resume.created_at.desc())
    )
    return list(database.scalars(statement))


def get_resume(database: Session, user: User, resume_id: uuid.UUID) -> Resume:
    return _get_owned_resume(database, user, resume_id)


def create_resume(
    database: Session,
    user: User,
    alias: str,
    uploaded_file: UploadFile,
) -> Resume:
    normalized_alias = alias.strip()
    if not normalized_alias:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Resume alias cannot be empty",
        )

    extension = Path(uploaded_file.filename or "").suffix.lower()
    allowed_mime_types = ALLOWED_FILE_TYPES.get(extension)
    if not allowed_mime_types or uploaded_file.content_type not in allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF and DOCX resume files are supported",
        )

    active_count = database.scalar(
        select(func.count()).select_from(Resume).where(
            Resume.user_id == user.id,
            Resume.deleted_at.is_(None),
        )
    )
    if active_count >= MAX_ACTIVE_RESUMES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student can keep at most five active resumes",
        )

    resume_id = uuid.uuid4()
    storage_name = f"{resume_id}{extension}"
    relative_storage_path = Path("uploads") / str(user.id) / storage_name
    absolute_storage_path = UPLOAD_DIRECTORY / str(user.id) / storage_name

    file_size = _save_upload(uploaded_file, absolute_storage_path)
    resume = Resume(
        id=resume_id,
        user_id=user.id,
        alias=normalized_alias,
        original_filename=Path(uploaded_file.filename or storage_name).name,
        mime_type=uploaded_file.content_type or "application/octet-stream",
        file_size_bytes=file_size,
        storage_path=str(relative_storage_path),
    )

    database.add(resume)
    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        absolute_storage_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active resume with this alias",
        ) from error

    database.refresh(resume)
    return resume


def update_resume(
    database: Session,
    user: User,
    resume_id: uuid.UUID,
    resume_update: ResumeUpdate,
) -> Resume:
    resume = _get_owned_resume(database, user, resume_id)
    changes = resume_update.model_dump(exclude_unset=True)

    if "alias" in changes:
        normalized_alias = changes["alias"].strip()
        if not normalized_alias:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Resume alias cannot be empty",
            )
        resume.alias = normalized_alias

    if changes.get("is_default") is True:
        database.execute(
            update(Resume)
            .where(
                Resume.user_id == user.id,
                Resume.id != resume.id,
                Resume.deleted_at.is_(None),
                Resume.is_default.is_(True),
            )
            .values(is_default=False)
        )
        resume.is_default = True
    elif changes.get("is_default") is False:
        resume.is_default = False

    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active resume with this alias",
        ) from error

    database.refresh(resume)
    return resume


def soft_delete_resume(database: Session, user: User, resume_id: uuid.UUID) -> None:
    resume = _get_owned_resume(database, user, resume_id)
    resume.deleted_at = datetime.now(UTC)
    resume.is_default = False
    database.commit()


def retry_resume_processing(database: Session, user: User, resume_id: uuid.UUID) -> Resume:
    resume = _get_owned_resume(database, user, resume_id)
    if resume.processing_status != ResumeProcessingStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only failed resumes can be retried",
        )

    resume.processing_status = ResumeProcessingStatus.UPLOADED
    resume.processing_error = None
    resume.processing_attempts = 0
    resume.processing_started_at = None
    resume.processing_completed_at = None
    resume.next_retry_at = None
    database.commit()
    database.refresh(resume)
    return resume


def _get_owned_resume(database: Session, user: User, resume_id: uuid.UUID) -> Resume:
    statement = select(Resume).where(
        Resume.id == resume_id,
        Resume.user_id == user.id,
        Resume.deleted_at.is_(None),
    )
    resume = database.scalar(statement)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found",
        )
    return resume


def _save_upload(uploaded_file: UploadFile, destination: Path) -> int:
    destination.parent.mkdir(parents=True, exist_ok=True)
    total_size = 0

    try:
        with destination.open("wb") as stored_file:
            while chunk := uploaded_file.file.read(1024 * 1024):
                total_size += len(chunk)
                if total_size > MAX_RESUME_SIZE_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Resume file must be 10 MB or smaller",
                    )
                stored_file.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        uploaded_file.file.close()

    if total_size == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Resume file cannot be empty",
        )

    return total_size
