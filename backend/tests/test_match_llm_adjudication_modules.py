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


def _adjudication(
    citations: list[str],
    requirement: str = "Vulnerability Research",
    extra_judgments: list[dict] | None = None,
    review_requirements: list[str] | None = None,
) -> LlmMatchAdjudicationOutput:
    return LlmMatchAdjudicationOutput.model_validate(
        {
            "requirement_judgments": [
                {
                    "requirement": requirement,
                    "requirement_category": "required_skill",
                    "support_level": "strong_partial",
                    "confidence": 0.8,
                    "cited_resume_section_keys": citations,
                    "reason": "The project demonstrates adjacent hands-on work.",
                }
            ]
            + (extra_judgments or []),
            "fairness_audit": {
                "assessment": "potentially_underestimated",
                "reason": "A missing requirement has partial evidence.",
                "review_requirements": review_requirements
                if review_requirements is not None
                else ["Vulnerability Research"],
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

    def test_judgment_maps_requirement_casing_back_to_expected_name(self) -> None:
        judgments = _validate_judgments(
            _adjudication(
                ["project:0:bullet:0"],
                requirement=" vulnerability   research ",
                review_requirements=[" vulnerability   research "],
            ),
            [("required_skill", "Vulnerability Research")],
            [_candidate()],
        )

        self.assertEqual(judgments[0].requirement, "Vulnerability Research")

    def test_judgment_deduplicates_identical_requirement_repeats(self) -> None:
        judgments = _validate_judgments(
            _adjudication(
                ["project:0:bullet:0"],
                extra_judgments=[
                    {
                        "requirement": "vulnerability research",
                        "requirement_category": "required_skill",
                        "support_level": "strong_partial",
                        "confidence": 0.7,
                        "cited_resume_section_keys": ["project:0:bullet:0"],
                        "reason": "Duplicate wording with different casing.",
                    }
                ],
            ),
            [("required_skill", "Vulnerability Research")],
            [_candidate()],
        )

        self.assertEqual(len(judgments), 1)

    def test_judgment_rejects_conflicting_duplicate_requirement(self) -> None:
        with self.assertRaises(HTTPException):
            _validate_judgments(
                _adjudication(
                    ["project:0:bullet:0"],
                    extra_judgments=[
                        {
                            "requirement": "vulnerability research",
                            "requirement_category": "required_skill",
                            "support_level": "absent",
                            "confidence": 0.9,
                            "cited_resume_section_keys": [],
                            "reason": "Conflicting duplicate.",
                        }
                    ],
                ),
                [("required_skill", "Vulnerability Research")],
                [_candidate()],
            )

    def test_judgment_fills_omitted_requirements_as_absent(self) -> None:
        judgments = _validate_judgments(
            _adjudication(["project:0:bullet:0"]),
            [
                ("required_skill", "Vulnerability Research"),
                ("preferred_skill", "PowerShell"),
            ],
            [_candidate()],
        )

        self.assertEqual(len(judgments), 2)
        omitted = next(judgment for judgment in judgments if judgment.requirement == "PowerShell")
        self.assertEqual(omitted.support_level, "absent")

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
