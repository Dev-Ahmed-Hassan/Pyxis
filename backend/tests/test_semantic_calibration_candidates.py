import unittest
import uuid
from unittest.mock import MagicMock, patch

from services.ai.config import ModelRoute
from services.semantic_calibration_candidate_service import (
    collect_semantic_calibration_candidates,
)


class SemanticCalibrationCandidateTests(unittest.TestCase):
    @patch("services.semantic_calibration_candidate_service.get_embedding_route")
    def test_exported_candidates_remain_pending_until_reviewed(self, route) -> None:
        route.return_value = ModelRoute("gemini", "gemini-embedding-001")
        database = MagicMock()
        database.execute.return_value.mappings.return_value = [
            {
                "requirement": "Backend Development",
                "section_type": "project",
                "section_key": "project:0",
                "section_text": "Built REST APIs",
                "cosine_similarity": 0.81234,
            }
        ]

        candidates = collect_semantic_calibration_candidates(
            database,
            uuid.uuid4(),
            uuid.uuid4(),
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].source, "pending_review")
        self.assertIsNone(candidates[0].should_report)
        self.assertEqual(candidates[0].cosine_similarity, 0.8123)
        self.assertTrue(candidates[0].id.startswith("live-"))


if __name__ == "__main__":
    unittest.main()
