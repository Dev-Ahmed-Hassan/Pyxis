"""Evaluate the deterministic matching engine against reviewed fixtures."""

import argparse
import json
import sys
from pathlib import Path

from services.matching_evaluation_service import (
    DEFAULT_FIXTURE_PATH,
    MatchingEvaluationReport,
    run_matching_evaluation,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate matching behavior against reviewed JSON fixtures."
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=DEFAULT_FIXTURE_PATH,
        help="Path to the matching-engine fixture JSON file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the complete evaluation report as JSON.",
    )
    arguments = parser.parse_args()

    try:
        report = run_matching_evaluation(arguments.fixtures)
    except Exception as error:
        print(f"Unable to run matching evaluation: {error}")
        return 1

    if arguments.json:
        print(report.model_dump_json(indent=2))
    else:
        _print_summary(report)
    return 0 if report.failed_cases == 0 else 1


def _print_summary(report: MatchingEvaluationReport) -> None:
    print(f"Matching engine evaluation: {report.score_version or 'mixed versions'}")
    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        detail = (
            f"overall={result.match.overall_score:.2f} "
            f"exact={result.match.exact_overlap_score:.2f} "
            f"related={result.match.related_skill_score.contribution_points:.2f}"
        )
        print(f"[{status}] {result.case_id} ({result.domain}): {detail}")
        for issue in result.issues:
            print(f"  - {issue}")
    print(
        f"Summary: {report.passed_cases}/{report.total_cases} passed, "
        f"{report.failed_cases} failed"
    )


if __name__ == "__main__":
    sys.exit(main())
