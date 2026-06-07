import time
from datetime import UTC, datetime, timedelta

from pymongo.errors import PyMongoError
from pydantic import ValidationError
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from database.mongodb import get_mongodb_database
from database.postgres import SessionLocal
from models.semantic_embedding_refresh_job import (
    SemanticEmbeddingRefreshJob,
    SemanticEmbeddingRefreshStatus,
)
from services.ai.internship_schemas import ParsedInternship
from services.ai.schemas import ParsedResume
from services.semantic_embedding_service import (
    BestEffortEmbeddingRefresh,
    best_effort_refresh_internship_requirement_embeddings,
    best_effort_refresh_resume_section_embeddings,
    invalidate_internship_requirement_embeddings,
    invalidate_resume_section_embeddings,
)

MAX_PROCESSING_ATTEMPTS = 5
POLL_INTERVAL_SECONDS = 3
STALE_PROCESSING_MINUTES = 10


def run_worker() -> None:
    print("Semantic embedding worker started. Press Ctrl+C to stop.")
    try:
        while True:
            processed_job = process_next_embedding_refresh()
            if not processed_job:
                time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("Semantic embedding worker stopped.")


def process_next_embedding_refresh() -> bool:
    with SessionLocal() as database:
        job = _claim_next_job(database)
        if not job:
            return False
        job_id = job.id
        _log(job, "claimed refresh job")
    _process_claimed_job(job_id)
    return True


def _claim_next_job(database: Session) -> SemanticEmbeddingRefreshJob | None:
    now = datetime.now(UTC)
    stale_before = now - timedelta(minutes=STALE_PROCESSING_MINUTES)
    statement = (
        select(SemanticEmbeddingRefreshJob)
        .where(
            SemanticEmbeddingRefreshJob.processing_attempts < MAX_PROCESSING_ATTEMPTS,
            or_(
                SemanticEmbeddingRefreshJob.status
                == SemanticEmbeddingRefreshStatus.QUEUED,
                and_(
                    SemanticEmbeddingRefreshJob.status
                    == SemanticEmbeddingRefreshStatus.RETRYING,
                    SemanticEmbeddingRefreshJob.next_retry_at <= now,
                ),
                and_(
                    SemanticEmbeddingRefreshJob.status
                    == SemanticEmbeddingRefreshStatus.PROCESSING,
                    SemanticEmbeddingRefreshJob.processing_started_at <= stale_before,
                ),
            ),
        )
        .order_by(SemanticEmbeddingRefreshJob.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    job = database.scalar(statement)
    if not job:
        return None
    job.status = SemanticEmbeddingRefreshStatus.PROCESSING
    job.processing_attempts += 1
    job.processing_error = None
    job.processing_started_at = now
    job.processing_completed_at = None
    job.next_retry_at = None
    database.commit()
    database.refresh(job)
    return job


def _process_claimed_job(job_id) -> None:
    with SessionLocal() as database:
        job = database.get(SemanticEmbeddingRefreshJob, job_id)
        if not job:
            return
        claimed_generation = job.generation
        try:
            result = _refresh_job(database, job)
            database.refresh(job)
            if job.generation != claimed_generation:
                _invalidate_obsolete_result(database, job)
                _log(job, "discarded obsolete refresh result")
                return
            if result.refreshed:
                job.status = SemanticEmbeddingRefreshStatus.COMPLETE
                job.processing_completed_at = datetime.now(UTC)
                job.next_retry_at = None
                _log(job, f"stored {result.document_count} embeddings")
            else:
                _mark_refresh_failure(job, result.warning or "Unknown refresh failure")
        except (PyMongoError, KeyError, ValidationError) as error:
            _mark_refresh_failure(job, str(error))
        database.commit()


def _invalidate_obsolete_result(
    database: Session,
    job: SemanticEmbeddingRefreshJob,
) -> None:
    if job.resume_id:
        invalidate_resume_section_embeddings(database, job.resume_id)
    else:
        invalidate_internship_requirement_embeddings(
            database,
            job.internship_input_id,
        )


def _refresh_job(
    database: Session,
    job: SemanticEmbeddingRefreshJob,
) -> BestEffortEmbeddingRefresh:
    mongodb = get_mongodb_database()
    if job.resume_id:
        document = mongodb.resumes.find_one(
            {"postgres_resume_id": str(job.resume_id)},
            {"parsed_resume": 1},
        )
        if not document:
            raise KeyError("Parsed resume document not found")
        return best_effort_refresh_resume_section_embeddings(
            database,
            job.resume_id,
            ParsedResume.model_validate(document["parsed_resume"]),
        )
    document = mongodb.internship_inputs.find_one(
        {"postgres_internship_id": str(job.internship_input_id)},
        {"parsed_internship": 1},
    )
    if not document:
        raise KeyError("Parsed internship document not found")
    return best_effort_refresh_internship_requirement_embeddings(
        database,
        job.internship_input_id,
        ParsedInternship.model_validate(document["parsed_internship"]),
    )


def _mark_refresh_failure(
    job: SemanticEmbeddingRefreshJob,
    error: str,
) -> None:
    job.processing_error = error[:1000]
    job.processing_completed_at = datetime.now(UTC)
    job.next_retry_at = _next_retry_time(job.processing_attempts)
    job.status = (
        SemanticEmbeddingRefreshStatus.RETRYING
        if job.next_retry_at
        else SemanticEmbeddingRefreshStatus.FAILED
    )
    _log(job, f"refresh failed: {error}; retry at {job.next_retry_at}")


def _next_retry_time(attempt_number: int) -> datetime | None:
    if attempt_number >= MAX_PROCESSING_ATTEMPTS:
        return None
    return datetime.now(UTC) + timedelta(minutes=2 ** (attempt_number - 1))


def _log(job: SemanticEmbeddingRefreshJob, message: str) -> None:
    source = f"resume {job.resume_id}" if job.resume_id else f"internship {job.internship_input_id}"
    print(f"[semantic embedding {source}] {message}", flush=True)


if __name__ == "__main__":
    run_worker()
