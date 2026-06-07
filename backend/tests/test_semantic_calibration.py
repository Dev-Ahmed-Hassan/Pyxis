import unittest

from pydantic import ValidationError

from services.semantic_calibration_service import (
    DEFAULT_SEMANTIC_FIXTURE_PATH,
    SemanticCalibrationCase,
    load_semantic_calibration_cases,
    run_semantic_calibration,
)


class SemanticCalibrationTests(unittest.TestCase):
    def test_starter_corpus_loads_labeled_cross_domain_observations(self) -> None:
        cases = load_semantic_calibration_cases()

        self.assertEqual(len(cases), 8)
        self.assertEqual(
            {case.domain for case in cases},
            {
                "cybersecurity",
                "software engineering",
                "networking",
                "data and AI",
                "QA and support",
                "cloud and DevOps",
            },
        )

    def test_report_keeps_synthetic_baseline_distinct_from_live_review(self) -> None:
        report = run_semantic_calibration()

        self.assertEqual(report.fixture_path, str(DEFAULT_SEMANTIC_FIXTURE_PATH))
        self.assertEqual(report.reviewed_live_cases, 0)
        self.assertEqual(report.labeled_cases, 8)
        self.assertEqual(report.synthetic_baseline_cases, 8)
        self.assertEqual(report.pending_review_cases, 0)
        self.assertEqual(report.current_threshold, 0.72)
        self.assertEqual(report.current_metrics.true_positive, 4)
        self.assertEqual(report.current_metrics.false_positive, 0)
        self.assertEqual(report.current_metrics.false_negative, 0)
        self.assertTrue(report.warnings)

    def test_pending_observation_cannot_be_accidentally_counted_as_reviewed(self) -> None:
        with self.assertRaises(ValidationError):
            SemanticCalibrationCase(
                id="pending",
                domain="review_me",
                resume_section="project",
                resume_text="Built APIs",
                requirement="Backend Development",
                cosine_similarity=0.8,
                should_report=True,
                source="pending_review",
                reviewer_note="",
            )


if __name__ == "__main__":
    unittest.main()
