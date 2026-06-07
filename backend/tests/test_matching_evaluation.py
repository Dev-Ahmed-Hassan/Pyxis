import unittest

from services.matching_evaluation_service import (
    DEFAULT_FIXTURE_PATH,
    load_evaluation_cases,
    run_matching_evaluation,
)


class MatchingEvaluationTests(unittest.TestCase):
    def test_reviewed_fixture_corpus_loads(self) -> None:
        cases = load_evaluation_cases()

        self.assertEqual(len(cases), 13)
        self.assertEqual(
            {case.domain for case in cases},
            {
                "software engineering",
                "data and AI",
                "cybersecurity",
                "networking",
                "cloud and DevOps",
                "QA and support",
            },
        )

    def test_current_engine_passes_reviewed_fixture_corpus(self) -> None:
        report = run_matching_evaluation()

        self.assertEqual(report.fixture_path, str(DEFAULT_FIXTURE_PATH))
        self.assertEqual(
            report.score_version,
            "separate-semantic-evidence-reporting-v6",
        )
        self.assertEqual(report.total_cases, 13)
        self.assertEqual(report.passed_cases, 13)
        self.assertEqual(report.failed_cases, 0)
        self.assertTrue(all(result.passed for result in report.results))

    def test_evaluation_uses_deterministic_synthetic_ids(self) -> None:
        first_report = run_matching_evaluation()
        second_report = run_matching_evaluation()

        self.assertEqual(
            [result.match.resume_id for result in first_report.results],
            [result.match.resume_id for result in second_report.results],
        )
        self.assertEqual(
            [result.match.internship_id for result in first_report.results],
            [result.match.internship_id for result in second_report.results],
        )


if __name__ == "__main__":
    unittest.main()
