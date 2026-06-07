import uuid

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def enqueue_resume_embedding_refresh(database: Session, resume_id: uuid.UUID) -> bool:
    return _best_effort_enqueue(
        database,
        """
        INSERT INTO public.semantic_embedding_refresh_jobs (resume_id)
        VALUES (:resume_id)
        ON CONFLICT (resume_id) WHERE resume_id IS NOT NULL
        DO UPDATE SET
            generation = gen_random_uuid(),
            status = 'queued',
            processing_attempts = 0,
            processing_error = NULL,
            processing_started_at = NULL,
            processing_completed_at = NULL,
            next_retry_at = NULL
        """,
        {"resume_id": resume_id},
    )


def enqueue_internship_embedding_refresh(
    database: Session,
    internship_id: uuid.UUID,
) -> bool:
    return _best_effort_enqueue(
        database,
        """
        INSERT INTO public.semantic_embedding_refresh_jobs (internship_input_id)
        VALUES (:internship_id)
        ON CONFLICT (internship_input_id) WHERE internship_input_id IS NOT NULL
        DO UPDATE SET
            generation = gen_random_uuid(),
            status = 'queued',
            processing_attempts = 0,
            processing_error = NULL,
            processing_started_at = NULL,
            processing_completed_at = NULL,
            next_retry_at = NULL
        """,
        {"internship_id": internship_id},
    )


def _best_effort_enqueue(
    database: Session,
    statement: str,
    parameters: dict,
) -> bool:
    try:
        database.execute(text(statement), parameters)
        database.commit()
        return True
    except SQLAlchemyError:
        database.rollback()
        return False
