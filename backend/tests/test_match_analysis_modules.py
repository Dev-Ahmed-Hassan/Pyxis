import unittest
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from schemas.matching import MatchAnalysisCreate
from services.analysis_staleness_service import (
    mark_internship_analyses_stale,
    mark_resume_analyses_stale,
)
from services.match_analysis_service import (
    create_match_analysis,
    get_match_analysis,
    list_match_analyses,
)
from services.matching_service import calculate_skill_match
from tests.test_matching_modules import _parsed_internship, _parsed_resume


class MatchAnalysisServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.user = SimpleNamespace(id=uuid.uuid4())
        self.resume_id = uuid.uuid4()
        self.internship_id = uuid.uuid4()
        self.analysis_session_id = uuid.uuid4()
        self.match = calculate_skill_match(
            resume_id=self.resume_id,
            internship_id=self.internship_id,
            parsed_resume=_parsed_resume("Python"),
            parsed_internship=_parsed_internship(required_skills=("Python",)),
        )

    @patch("services.match_analysis_service.get_match_preview")
    def test_create_analysis_persists_versioned_payload(self, get_match_preview) -> None:
        get_match_preview.return_value = self.match
        database = MagicMock()
        created_at = datetime.now(UTC)

        def refresh(analysis) -> None:
            analysis.id = uuid.uuid4()
            analysis.created_at = created_at
            analysis.stale_at = None

        database.refresh.side_effect = refresh

        response = create_match_analysis(
            database,
            self.user,
            MatchAnalysisCreate(
                resume_id=self.resume_id,
                internship_id=self.internship_id,
                analysis_session_id=self.analysis_session_id,
            ),
        )

        stored_analysis = database.add.call_args.args[0]
        self.assertEqual(stored_analysis.user_id, self.user.id)
        self.assertEqual(stored_analysis.analysis_session_id, self.analysis_session_id)
        self.assertEqual(stored_analysis.score_version, self.match.score_version)
        self.assertEqual(
            stored_analysis.analysis_payload["resume_skill_evidence"][0]["skill"],
            "Python",
        )
        self.assertEqual(response.match, self.match)
        database.commit.assert_called_once_with()

    def test_list_analyses_returns_stored_payloads(self) -> None:
        database = MagicMock()
        stored_analysis = SimpleNamespace(
            id=uuid.uuid4(),
            resume_id=self.resume_id,
            internship_input_id=self.internship_id,
            analysis_session_id=self.analysis_session_id,
            score_version=self.match.score_version,
            overall_score=self.match.overall_score,
            analysis_payload=self.match.model_dump(mode="json"),
            created_at=datetime.now(UTC),
            stale_at=None,
        )
        database.scalars.return_value = [stored_analysis]

        responses = list_match_analyses(database, self.user)

        self.assertEqual(len(responses), 1)
        self.assertEqual(responses[0].match, self.match)

    def test_get_analysis_returns_404_for_unowned_or_missing_row(self) -> None:
        database = MagicMock()
        database.scalar.return_value = None

        with self.assertRaises(HTTPException) as context:
            get_match_analysis(database, self.user, uuid.uuid4())

        self.assertEqual(context.exception.status_code, 404)


class MatchAnalysisStalenessTests(unittest.TestCase):
    def test_resume_staleness_update_targets_resume(self) -> None:
        database = MagicMock()

        mark_resume_analyses_stale(database, uuid.uuid4())

        statements = [str(call.args[0]) for call in database.execute.call_args_list]
        self.assertIn("UPDATE match_analyses", statements[0])
        self.assertIn("match_analyses.resume_id", statements[0])
        self.assertIn("match_analyses.stale_at IS NULL", statements[0])
        self.assertIn("UPDATE match_llm_adjudications", statements[1])
        self.assertIn("match_llm_adjudications.resume_id", statements[1])

    def test_internship_staleness_update_targets_internship(self) -> None:
        database = MagicMock()

        mark_internship_analyses_stale(database, uuid.uuid4())

        statements = [str(call.args[0]) for call in database.execute.call_args_list]
        self.assertIn("UPDATE match_analyses", statements[0])
        self.assertIn("match_analyses.internship_input_id", statements[0])
        self.assertIn("match_analyses.stale_at IS NULL", statements[0])
        self.assertIn("UPDATE match_llm_adjudications", statements[1])
        self.assertIn("match_llm_adjudications.internship_input_id", statements[1])


if __name__ == "__main__":
    unittest.main()
