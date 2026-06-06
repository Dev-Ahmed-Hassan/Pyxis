import time
from datetime import UTC, datetime, timedelta

from pymongo.errors import PyMongoError
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from database.mongodb import get_mongodb_database
from database.postgres import SessionLocal
from models.internship import InternshipInput, InternshipProcessingStatus
from services.internship_parsing_service import (
    INTERNSHIP_PARSER_VERSION,
    InternshipParsingError,
    TemporaryInternshipParsingError,
    parse_and_store_internship,
)
from services.analysis_staleness_service import mark_internship_analyses_stale
from services.semantic_embedding_service import (
    invalidate_internship_requirement_embeddings,
)
from services.semantic_embedding_queue_service import (
    enqueue_internship_embedding_refresh,
)

MAX_PROCESSING_ATTEMPTS = 3
POLL_INTERVAL_SECONDS = 3
STALE_PROCESSING_MINUTES = 10


def run_worker() -> None:
    print("Internship worker started. Press Ctrl+C to stop.")
    try:
        while True:
            processed_internship = process_next_internship()
            if not processed_internship:
                time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Internship worker stopped.")


def process_next_internship() -> bool:
    with SessionLocal() as database:
        internship = _claim_next_internship(database)
        if not internship:
            return False
        internship_id = internship.id
        _log(internship_id, f"claimed job at stage '{internship.processing_status.value}'")

    _process_claimed_internship(internship_id)
    return True


def _claim_next_internship(database: Session) -> InternshipInput | None:
    now = datetime.now(UTC)
    stale_before = now - timedelta(minutes=STALE_PROCESSING_MINUTES)
    statement = (
        select(InternshipInput)
        .where(
            InternshipInput.deleted_at.is_(None),
            InternshipInput.processing_attempts < MAX_PROCESSING_ATTEMPTS,
            or_(
                InternshipInput.processing_status == InternshipProcessingStatus.SUBMITTED,
                and_(
                    InternshipInput.processing_status == InternshipProcessingStatus.FAILED,
                    InternshipInput.next_retry_at.is_not(None),
                    InternshipInput.next_retry_at <= now,
                ),
                and_(
                    InternshipInput.processing_status.in_(
                        [
                            InternshipProcessingStatus.PARSING,
                            InternshipProcessingStatus.VALIDATING,
                        ]
                    ),
                    InternshipInput.processing_started_at.is_not(None),
                    InternshipInput.processing_started_at <= stale_before,
                ),
            ),
        )
        .order_by(InternshipInput.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    internship = database.scalar(statement)
    if not internship:
        return None

    internship.processing_status = InternshipProcessingStatus.PARSING
    internship.processing_error = None
    internship.processing_attempts += 1
    internship.processing_started_at = now
    internship.processing_completed_at = None
    internship.next_retry_at = None
    database.commit()
    database.refresh(internship)
    return internship


def _process_claimed_internship(internship_id) -> None:
    with SessionLocal() as database:
        internship = database.get(InternshipInput, internship_id)
        if not internship or internship.deleted_at is not None:
            return

        try:
            mongodb = get_mongodb_database()
            _log(internship.id, "parsing internship through configured AI providers")
            (
                internship.mongo_document_id,
                _,
            ) = parse_and_store_internship(internship, mongodb)
            internship.processing_status = InternshipProcessingStatus.VALIDATING
            database.commit()
            _log(internship.id, "validated structured AI response")

            invalidate_internship_requirement_embeddings(database, internship.id)
            mark_internship_analyses_stale(database, internship.id)
            database.commit()
            if enqueue_internship_embedding_refresh(database, internship.id):
                _log(internship.id, "queued semantic requirement embedding refresh")
            else:
                _log(internship.id, "semantic embedding queue is unavailable")

            internship.processing_status = InternshipProcessingStatus.READY
            internship.parser_version = INTERNSHIP_PARSER_VERSION
            internship.processing_completed_at = datetime.now(UTC)
            internship.next_retry_at = None
            _log(internship.id, "completed processing with status 'ready'")
        except TemporaryInternshipParsingError as error:
            internship.processing_status = InternshipProcessingStatus.FAILED
            internship.processing_error = str(error)
            internship.processing_completed_at = datetime.now(UTC)
            internship.next_retry_at = _next_retry_time(internship.processing_attempts)
            _log(internship.id, f"temporary AI failure: {error}; retry at {internship.next_retry_at}")
        except InternshipParsingError as error:
            internship.processing_status = InternshipProcessingStatus.FAILED
            internship.processing_error = str(error)
            internship.processing_completed_at = datetime.now(UTC)
            internship.next_retry_at = None
            _log(internship.id, f"permanent AI parsing failure: {error}")
        except PyMongoError as error:
            internship.processing_status = InternshipProcessingStatus.FAILED
            internship.processing_error = "Internship document storage is temporarily unavailable"
            internship.processing_completed_at = datetime.now(UTC)
            internship.next_retry_at = _next_retry_time(internship.processing_attempts)
            _log(
                internship.id,
                f"temporary MongoDB failure ({type(error).__name__}); retry at {internship.next_retry_at}",
            )

        database.commit()


def _next_retry_time(attempt_number: int) -> datetime | None:
    if attempt_number >= MAX_PROCESSING_ATTEMPTS:
        return None
    delay_minutes = 2 ** (attempt_number - 1)
    return datetime.now(UTC) + timedelta(minutes=delay_minutes)


def _log(internship_id, message: str) -> None:
    print(f"[internship {internship_id}] {message}", flush=True)


if __name__ == "__main__":
    run_worker()
