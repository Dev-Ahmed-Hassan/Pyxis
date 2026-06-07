import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from sqlalchemy.exc import SQLAlchemyError

from models.semantic_embedding_refresh_job import SemanticEmbeddingRefreshStatus
from services.semantic_embedding_queue_service import (
    enqueue_internship_embedding_refresh,
    enqueue_resume_embedding_refresh,
)
from workers.semantic_embedding_worker import (
    _mark_refresh_failure,
    _next_retry_time,
    _process_claimed_job,
)
from services.semantic_embedding_service import BestEffortEmbeddingRefresh


class SemanticEmbeddingQueueServiceTests(unittest.TestCase):
    def test_resume_enqueue_resets_existing_job_to_latest_source_state(self) -> None:
        database = MagicMock()
        resume_id = uuid.uuid4()

        queued = enqueue_resume_embedding_refresh(database, resume_id)

        self.assertTrue(queued)
        statement = str(database.execute.call_args.args[0])
        self.assertIn("ON CONFLICT (resume_id)", statement)
        self.assertIn("generation = gen_random_uuid()", statement)
        self.assertIn("processing_attempts = 0", statement)
        self.assertEqual(database.execute.call_args.args[1], {"resume_id": resume_id})
        database.commit.assert_called_once_with()

    def test_internship_enqueue_is_best_effort_during_migration_rollout(self) -> None:
        database = MagicMock()
        database.execute.side_effect = SQLAlchemyError("missing queue table")

        queued = enqueue_internship_embedding_refresh(database, uuid.uuid4())

        self.assertFalse(queued)
        database.rollback.assert_called_once_with()


class SemanticEmbeddingWorkerTests(unittest.TestCase):
    @patch("workers.semantic_embedding_worker._invalidate_obsolete_result")
    @patch("workers.semantic_embedding_worker._refresh_job")
    @patch("workers.semantic_embedding_worker.SessionLocal")
    def test_obsolete_worker_result_is_invalidated_instead_of_marked_complete(
        self,
        session_local,
        refresh_job,
        invalidate,
    ) -> None:
        claimed_generation = uuid.uuid4()
        job = SimpleNamespace(
            id=uuid.uuid4(),
            generation=claimed_generation,
            resume_id=uuid.uuid4(),
            internship_input_id=None,
            status=SemanticEmbeddingRefreshStatus.PROCESSING,
        )
        database = MagicMock()
        database.get.return_value = job

        def refresh_generation(_) -> None:
            job.generation = uuid.uuid4()

        database.refresh.side_effect = refresh_generation
        session_local.return_value.__enter__.return_value = database
        refresh_job.return_value = BestEffortEmbeddingRefresh(
            refreshed=True,
            document_count=2,
        )

        _process_claimed_job(job.id)

        invalidate.assert_called_once_with(database, job)
        self.assertNotEqual(job.status, SemanticEmbeddingRefreshStatus.COMPLETE)

    @patch("workers.semantic_embedding_worker._next_retry_time")
    def test_refresh_failure_records_retry_without_breaking_source_profile(
        self,
        next_retry,
    ) -> None:
        retry_at = SimpleNamespace()
        next_retry.return_value = retry_at
        job = SimpleNamespace(
            resume_id=uuid.uuid4(),
            internship_input_id=None,
            processing_attempts=1,
            processing_error=None,
            processing_completed_at=None,
            next_retry_at=None,
            status=SemanticEmbeddingRefreshStatus.PROCESSING,
        )

        _mark_refresh_failure(job, "provider temporarily unavailable")

        self.assertEqual(job.status, SemanticEmbeddingRefreshStatus.RETRYING)
        self.assertEqual(job.next_retry_at, retry_at)
        self.assertEqual(job.processing_error, "provider temporarily unavailable")

    def test_retry_schedule_stops_after_maximum_attempts(self) -> None:
        self.assertIsNone(_next_retry_time(5))


if __name__ == "__main__":
    unittest.main()
