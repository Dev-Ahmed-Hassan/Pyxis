import time
from datetime import UTC, datetime, timedelta

from pymongo.errors import PyMongoError
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from database.mongodb import get_mongodb_database
from database.postgres import SessionLocal
from models.resume import Resume, ResumeProcessingStatus
from services.resume_extraction_service import ResumeExtractionError, extract_and_store_resume_text
from services.resume_parsing_service import (
    PARSER_VERSION,
    ResumeParsingError,
    TemporaryResumeParsingError,
    parse_and_store_resume,
)

MAX_PROCESSING_ATTEMPTS = 3
POLL_INTERVAL_SECONDS = 3
STALE_PROCESSING_MINUTES = 10


def run_worker() -> None:
    print("Resume worker started. Press Ctrl+C to stop.")
    try:
        while True:
            processed_resume = process_next_resume()
            if not processed_resume:
                time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Resume worker stopped.")


def process_next_resume() -> bool:
    with SessionLocal() as database:
        resume = _claim_next_resume(database)
        if not resume:
            return False
        resume_id = resume.id
        _log(resume_id, f"claimed job at stage '{resume.processing_status.value}'")

    _process_claimed_resume(resume_id)
    return True


def _claim_next_resume(database: Session) -> Resume | None:
    now = datetime.now(UTC)
    stale_before = now - timedelta(minutes=STALE_PROCESSING_MINUTES)

    statement = (
        select(Resume)
        .where(
            Resume.deleted_at.is_(None),
            Resume.processing_attempts < MAX_PROCESSING_ATTEMPTS,
            or_(
                Resume.processing_status == ResumeProcessingStatus.UPLOADED,
                Resume.processing_status == ResumeProcessingStatus.TEXT_EXTRACTED,
                and_(
                    Resume.processing_status == ResumeProcessingStatus.FAILED,
                    Resume.next_retry_at.is_not(None),
                    Resume.next_retry_at <= now,
                ),
                and_(
                    Resume.processing_status.in_(
                        [
                            ResumeProcessingStatus.EXTRACTING_TEXT,
                            ResumeProcessingStatus.PARSING,
                            ResumeProcessingStatus.VALIDATING,
                            ResumeProcessingStatus.EMBEDDING,
                        ]
                    ),
                    Resume.processing_started_at.is_not(None),
                    Resume.processing_started_at <= stale_before,
                ),
            ),
        )
        .order_by(Resume.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    resume = database.scalar(statement)
    if not resume:
        return None

    if resume.processing_status == ResumeProcessingStatus.TEXT_EXTRACTED:
        resume.processing_status = ResumeProcessingStatus.PARSING
    else:
        resume.processing_status = ResumeProcessingStatus.EXTRACTING_TEXT
    resume.processing_error = None
    resume.processing_attempts += 1
    resume.processing_started_at = now
    resume.processing_completed_at = None
    resume.next_retry_at = None
    database.commit()
    database.refresh(resume)
    return resume


def _process_claimed_resume(resume_id) -> None:
    with SessionLocal() as database:
        resume = database.get(Resume, resume_id)
        if not resume or resume.deleted_at is not None:
            return

        try:
            mongodb = get_mongodb_database()
            if resume.processing_status == ResumeProcessingStatus.EXTRACTING_TEXT:
                _log(resume.id, "extracting resume text")
                resume.mongo_document_id = extract_and_store_resume_text(resume, mongodb)
                resume.processing_status = ResumeProcessingStatus.TEXT_EXTRACTED
                resume.processing_error = None
                database.commit()
                _log(resume.id, "stored extracted text in MongoDB")

            resume.processing_status = ResumeProcessingStatus.PARSING
            database.commit()
            _log(resume.id, "parsing resume through configured AI providers")

            parse_and_store_resume(str(resume.id), mongodb)
            resume.processing_status = ResumeProcessingStatus.VALIDATING
            database.commit()
            _log(resume.id, "validated structured AI response")

            resume.processing_status = ResumeProcessingStatus.READY
            resume.parser_version = PARSER_VERSION
            resume.processing_completed_at = datetime.now(UTC)
            resume.next_retry_at = None
            _log(resume.id, "completed processing with status 'ready'")
        except ResumeExtractionError as error:
            resume.processing_status = ResumeProcessingStatus.FAILED
            resume.processing_error = str(error)
            resume.processing_completed_at = datetime.now(UTC)
            resume.next_retry_at = None
            _log(resume.id, f"permanent extraction failure: {error}")
        except TemporaryResumeParsingError as error:
            resume.processing_status = ResumeProcessingStatus.FAILED
            resume.processing_error = str(error)
            resume.processing_completed_at = datetime.now(UTC)
            resume.next_retry_at = _next_retry_time(resume.processing_attempts)
            _log(resume.id, f"temporary AI failure: {error}; retry at {resume.next_retry_at}")
        except ResumeParsingError as error:
            resume.processing_status = ResumeProcessingStatus.FAILED
            resume.processing_error = str(error)
            resume.processing_completed_at = datetime.now(UTC)
            resume.next_retry_at = None
            _log(resume.id, f"permanent AI parsing failure: {error}")
        except PyMongoError as error:
            resume.processing_status = ResumeProcessingStatus.FAILED
            resume.processing_error = "Resume text storage is temporarily unavailable"
            resume.processing_completed_at = datetime.now(UTC)
            resume.next_retry_at = _next_retry_time(resume.processing_attempts)
            _log(
                resume.id,
                f"temporary MongoDB failure ({type(error).__name__}); retry at {resume.next_retry_at}",
            )

        database.commit()


def _next_retry_time(attempt_number: int) -> datetime | None:
    if attempt_number >= MAX_PROCESSING_ATTEMPTS:
        return None
    delay_minutes = 2 ** (attempt_number - 1)
    return datetime.now(UTC) + timedelta(minutes=delay_minutes)


def _log(resume_id, message: str) -> None:
    print(f"[resume {resume_id}] {message}", flush=True)


if __name__ == "__main__":
    run_worker()
