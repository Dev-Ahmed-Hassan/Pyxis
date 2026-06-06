import unittest
import uuid

from fastapi import HTTPException

from schemas.matching import LlmRetrievedEvidence
from services.ai.matching_adjudication_schemas import LlmMatchAdjudicationOutput
from services.match_llm_adjudication_service import (
    _build_prompt,
    _calculate_shadow_credits,
    _validate_judgments,
)
from services.matching_service import calculate_skill_match
from tests.test_matching_modules import _parsed_internship, _parsed_resume


def _candidate() -> LlmRetrievedEvidence:
    return LlmRetrievedEvidence(
        requirement="Vulnerability Research",
        requirement_category="required_skill",
        resume_section="project",
        resume_section_key="project:0:bullet:0",
        resume_text_excerpt="Investigated findings from vulnerability scans",
        cosine_similarity=0.68,
        source="pgvector",
    )


def _adjudication(citations: list[str]) -> LlmMatchAdjudicationOutput:
    return LlmMatchAdjudicationOutput.model_validate(
        {
            "requirement_judgments": [
                {
                    "requirement": "Vulnerability Research",
                    "requirement_category": "required_skill",
                    "support_level": "strong_partial",
                    "confidence": 0.8,
                    "cited_resume_section_keys": citations,
                    "reason": "The project demonstrates adjacent hands-on work.",
                }
            ],
            "fairness_audit": {
                "assessment": "potentially_underestimated",
                "reason": "A missing requirement has partial evidence.",
                "review_requirements": ["Vulnerability Research"],
            },
        }
    )


class MatchLlmAdjudicationTests(unittest.TestCase):
    def test_prompt_uses_compact_audit_context(self) -> None:
        resume = _parsed_resume("Python")
        resume.summary.value = "DO_NOT_SEND_FULL_RESUME_SUMMARY"
        internship = _parsed_internship(required_skills=("Vulnerability Research",))
        match = calculate_skill_match(
            uuid.uuid4(),
            uuid.uuid4(),
            resume,
            internship,
        )

        prompt = _build_prompt(match, resume, internship, [_candidate()])

        self.assertIn("audit_context", prompt)
        self.assertIn("official_score", prompt)
        self.assertIn("Vulnerability Research", prompt)
        self.assertNotIn("parsed_resume", prompt)
        self.assertNotIn("DO_NOT_SEND_FULL_RESUME_SUMMARY", prompt)

    def test_judgment_accepts_only_retrieved_resume_citations(self) -> None:
        judgments = _validate_judgments(
            _adjudication(["project:0:bullet:0"]),
            [("required_skill", "Vulnerability Research")],
            [_candidate()],
        )

        self.assertEqual(judgments[0].support_level, "strong_partial")

    def test_supported_judgment_requires_a_citation(self) -> None:
        with self.assertRaises(HTTPException):
            _validate_judgments(
                _adjudication([]),
                [("required_skill", "Vulnerability Research")],
                [_candidate()],
            )

    def test_judgment_rejects_citations_outside_retrieval(self) -> None:
        with self.assertRaises(HTTPException):
            _validate_judgments(
                _adjudication(["project:9"]),
                [("required_skill", "Vulnerability Research")],
                [_candidate()],
            )

    def test_fairness_audit_rejects_requirements_outside_review_set(self) -> None:
        adjudication = _adjudication(["project:0:bullet:0"])
        adjudication.fairness_audit.review_requirements = ["Unrelated Requirement"]

        with self.assertRaises(HTTPException):
            _validate_judgments(
                adjudication,
                [("required_skill", "Vulnerability Research")],
                [_candidate()],
            )

    def test_shadow_credit_is_bounded_and_does_not_modify_official_score(self) -> None:
        match = calculate_skill_match(
            uuid.uuid4(),
            uuid.uuid4(),
            _parsed_resume(),
            _parsed_internship(required_skills=("Vulnerability Research",)),
        )
        judgments = _validate_judgments(
            _adjudication(["project:0:bullet:0"]),
            [("required_skill", "Vulnerability Research")],
            [_candidate()],
        )

        credits = _calculate_shadow_credits(match, judgments)

        self.assertEqual(match.overall_score, 0.0)
        self.assertEqual(credits[0].credit_factor, 0.3)
        self.assertEqual(credits[0].contribution_points, 30.0)


if __name__ == "__main__":
    unittest.main()
