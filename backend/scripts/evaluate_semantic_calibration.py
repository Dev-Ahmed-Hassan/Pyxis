"""Report semantic-evidence threshold behavior against labeled observations."""

import argparse
import json
import sys
from pathlib import Path

from services.semantic_calibration_service import (
    DEFAULT_SEMANTIC_FIXTURE_PATH,
    SemanticCalibrationReport,
    run_semantic_calibration,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate semantic-evidence reporting thresholds."
    )
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=DEFAULT_SEMANTIC_FIXTURE_PATH,
        help="Path to semantic calibration fixture JSON.",
    )
    parser.add_argument("--json", action="store_true")
    arguments = parser.parse_args()
    try:
        report = run_semantic_calibration(arguments.fixtures)
    except Exception as error:
        print(f"Unable to evaluate semantic calibration: {error}")
        return 1
    if arguments.json:
        print(report.model_dump_json(indent=2))
    else:
        _print_summary(report)
    return 0


def _print_summary(report: SemanticCalibrationReport) -> None:
    print(
        "Semantic evidence calibration: "
        f"{report.total_cases} observations, {report.labeled_cases} labeled "
        f"({report.reviewed_live_cases} reviewed live, "
        f"{report.synthetic_baseline_cases} synthetic baseline, "
        f"{report.pending_review_cases} pending review)"
    )
    for metric in report.candidate_metrics:
        marker = " current" if metric.threshold == report.current_threshold else ""
        print(
            f"threshold={metric.threshold:.2f}{marker}: "
            f"precision={metric.precision:.4f} recall={metric.recall:.4f} "
            f"f1={metric.f1:.4f} "
            f"tp={metric.true_positive} fp={metric.false_positive} "
            f"tn={metric.true_negative} fn={metric.false_negative}"
        )
    for warning in report.warnings:
        print(f"WARNING: {warning}")


if __name__ == "__main__":
    sys.exit(main())
