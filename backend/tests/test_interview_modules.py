import unittest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from schemas.profile import UserProfileFactsResponse
from services.ai.interview_schemas import NextQuestionDecisionOutput
from services.interview_context_service import _build_candidate
from services.interview_session_service import (
    _create_follow_up_question,
    _should_generate_follow_up,
    get_next_question,
    submit_answer,
)


class _ScalarDatabase:
    def __init__(self, values):
        self.values = iter(values)
        self.added = []
        self.commits = 0

    def scalar(self, _statement):
        return next(self.values)

    def add(self, value):
        self.added.append(value)

    def commit(self):
        self.commits += 1

    def refresh(self, value):
        if getattr(value, "created_at", None) is None:
            value.created_at = datetime.now(timezone.utc)


class InterviewModuleTests(unittest.TestCase):
    def test_candidate_context_uses_only_the_selected_resume(self) -> None:
        selected_resume_id = uuid.uuid4()
        other_resume_id = uuid.uuid4()
        profile = UserProfileFactsResponse.model_validate(
            {
                "user_id": uuid.uuid4(),
                "skill_inventory": [],
                "skill_sources": [
                    {
                        "id": uuid.uuid4(),
                        "resume_id": selected_resume_id,
                        "skill_name": "Python",
                        "canonical_name": "Python",
                        "source_section": "experience",
                        "source_key": "experience:0:skill:0",
                        "extraction_source": "explicit",
                        "confidence": 0.9,
                        "evidence": "Built API services.",
                        "context": "Backend Intern - Example Co",
                        "created_at": datetime.now(timezone.utc),
                    },
                    {
                        "id": uuid.uuid4(),
                        "resume_id": other_resume_id,
                        "skill_name": "Java",
                        "canonical_name": "Java",
                        "source_section": "experience",
                        "source_key": "experience:0:skill:0",
                        "extraction_source": "explicit",
                        "confidence": 0.9,
                        "evidence": "Maintained Java services.",
                        "context": "Other Resume Experience",
                        "created_at": datetime.now(timezone.utc),
                    },
                ],
                "project_sources": [
                    {
                        "id": uuid.uuid4(),
                        "resume_id": selected_resume_id,
                        "source_key": "project:0",
                        "project_name": "Security Monitor",
                        "description": ["Detected suspicious traffic."],
                        "skills": ["Python", "Wireshark"],
                        "confidence": 0.9,
                        "evidence": "Resume project",
                        "created_at": datetime.now(timezone.utc),
                    },
                    {
                        "id": uuid.uuid4(),
                        "resume_id": other_resume_id,
                        "source_key": "project:0",
                        "project_name": "Unrelated Project",
                        "description": [],
                        "skills": ["Java"],
                        "confidence": 0.9,
                        "evidence": None,
                        "created_at": datetime.now(timezone.utc),
                    },
                ],
                "certification_sources": [
                    {
                        "id": uuid.uuid4(),
                        "resume_id": selected_resume_id,
                        "source_key": "certification:0",
                        "certification_name": "Security+",
                        "issuer": "CompTIA",
                        "date": "2026",
                        "confidence": 0.9,
                        "evidence": "Resume certification",
                        "created_at": datetime.now(timezone.utc),
                    }
                ],
            }
        )
        match = SimpleNamespace(resume_skills=["Python", "Wireshark"])

        candidate = _build_candidate(match, profile, selected_resume_id)

        self.assertEqual(candidate["projects"][0]["name"], "Security Monitor")
        self.assertEqual(candidate["certifications"][0]["name"], "Security+")
        self.assertEqual(candidate["experience"][0]["label"], "Backend Intern - Example Co")
        self.assertNotIn("Unrelated Project", str(candidate))
        self.assertNotIn("Other Resume Experience", str(candidate))

    def test_follow_up_is_allowed_only_after_a_planned_question(self) -> None:
        planned = SimpleNamespace(is_follow_up=False)
        follow_up = SimpleNamespace(is_follow_up=True)
        answer = SimpleNamespace(private_assessment={"follow_up_needed": True})

        self.assertTrue(_should_generate_follow_up(planned, answer))
        self.assertFalse(_should_generate_follow_up(follow_up, answer))

    def test_follow_up_requires_complete_generated_question_data(self) -> None:
        with self.assertRaises(HTTPException):
            _create_follow_up_question(
                SimpleNamespace(id=uuid.uuid4()),
                SimpleNamespace(
                    id=uuid.uuid4(),
                    sequence_number=1,
                    source_requirement=None,
                    source_section_keys=None,
                ),
                NextQuestionDecisionOutput(
                    decision="follow_up",
                    follow_up_question_text=None,
                    follow_up_category=None,
                    follow_up_reason=None,
                ),
            )

    @patch("services.interview_session_service._run_next_question_decision")
    def test_next_question_creates_an_adaptive_follow_up(self, run_decision) -> None:
        session_id = uuid.uuid4()
        user_id = uuid.uuid4()
        question_id = uuid.uuid4()
        session = SimpleNamespace(
            id=session_id,
            user_id=user_id,
            status="in_progress",
            current_question_number=1,
            question_target=5,
            rolling_summary="Candidate discussed Python.",
        )
        question = SimpleNamespace(
            id=question_id,
            session_id=session_id,
            sequence_number=1,
            category="resume_project",
            question_text="Explain your project.",
            reason="Validate project depth.",
            source_requirement="Python",
            source_section_keys=["project:0"],
            is_follow_up=False,
            parent_question_id=None,
            created_at=datetime.now(timezone.utc),
        )
        answer = SimpleNamespace(
            answer_text="I built it using Python and FastAPI.",
            private_assessment={"follow_up_needed": True},
        )
        run_decision.return_value = (
            NextQuestionDecisionOutput(
                decision="follow_up",
                follow_up_question_text="What technical trade-off did you make?",
                follow_up_category="resume_project",
                follow_up_reason="Clarify the candidate's engineering decisions.",
            ),
            "gemini",
            "model",
        )
        database = _ScalarDatabase([session, question, answer])

        response = get_next_question(
            database,
            SimpleNamespace(id=user_id),
            session_id,
        )

        self.assertTrue(response.is_follow_up)
        self.assertEqual(response.question.parent_question_id, question_id)
        self.assertEqual(response.questions_remaining, 4)
        self.assertEqual(database.commits, 1)
        self.assertEqual(len(database.added), 1)

    @patch("services.interview_session_service._run_rolling_summary")
    @patch("services.interview_session_service._run_private_assessment")
    def test_follow_up_answer_cannot_request_another_follow_up(
        self,
        run_assessment,
        run_summary,
    ) -> None:
        session_id = uuid.uuid4()
        question_id = uuid.uuid4()
        user_id = uuid.uuid4()
        session = SimpleNamespace(
            id=session_id,
            user_id=user_id,
            status="in_progress",
            current_question_number=5,
            question_target=5,
            rolling_summary="Existing summary",
            completed_at=None,
        )
        question = SimpleNamespace(
            id=question_id,
            session_id=session_id,
            is_follow_up=True,
        )
        run_assessment.return_value = (
            SimpleNamespace(
                follow_up_needed=True,
                model_dump=lambda mode: {"follow_up_needed": True},
            ),
            "gemini",
            "model",
        )
        run_summary.return_value = (
            SimpleNamespace(updated_summary="Updated summary"),
            "gemini",
            "model",
        )
        database = _ScalarDatabase([session, question, None])

        response = submit_answer(
            database,
            SimpleNamespace(id=user_id),
            session_id,
            SimpleNamespace(
                question_id=question_id,
                answer_text="A sufficiently detailed follow-up answer.",
            ),
        )

        self.assertFalse(response.next_is_follow_up)
        self.assertTrue(response.session_complete)
        self.assertEqual(session.status, "completed")


if __name__ == "__main__":
    unittest.main()
