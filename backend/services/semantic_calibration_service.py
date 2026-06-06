import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from services.semantic_matching_service import SEMANTIC_EVIDENCE_THRESHOLD

DEFAULT_SEMANTIC_FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "fixtures"
    / "semantic_calibration_cases.json"
)
DEFAULT_CANDIDATE_THRESHOLDS = (0.60, 0.65, 0.70, 0.72, 0.75, 0.80)


class SemanticCalibrationCase(BaseModel):
    id: str
    domain: str
    resume_section: Literal["summary", "project", "experience", "education"]
    resume_text: str
    requirement: str
    cosine_similarity: float = Field(ge=-1.0, le=1.0)
    should_report: bool | None
    source: Literal["synthetic_baseline", "reviewed_live", "pending_review"]
    reviewer_note: str

    @model_validator(mode="after")
    def validate_review_state(self):
        if self.source == "pending_review" and self.should_report is not None:
            raise ValueError("pending_review observations must remain unlabeled")
        if self.source != "pending_review" and self.should_report is None:
            raise ValueError("reviewed calibration observations require a label")
        return self


class SemanticThresholdMetrics(BaseModel):
    threshold: float
    true_positive: int
    false_positive: int
    true_negative: int
    false_negative: int
    precision: float
    recall: float
    f1: float


class SemanticCalibrationReport(BaseModel):
    fixture_path: str
    total_cases: int
    labeled_cases: int
    reviewed_live_cases: int
    synthetic_baseline_cases: int
    pending_review_cases: int
    current_threshold: float
    current_metrics: SemanticThresholdMetrics
    candidate_metrics: list[SemanticThresholdMetrics]
    warnings: list[str]


def load_semantic_calibration_cases(
    fixture_path: Path = DEFAULT_SEMANTIC_FIXTURE_PATH,
) -> list[SemanticCalibrationCase]:
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    return [
        SemanticCalibrationCase.model_validate(case)
        for case in data["cases"]
    ]


def run_semantic_calibration(
    fixture_path: Path = DEFAULT_SEMANTIC_FIXTURE_PATH,
    thresholds: tuple[float, ...] = DEFAULT_CANDIDATE_THRESHOLDS,
) -> SemanticCalibrationReport:
    cases = load_semantic_calibration_cases(fixture_path)
    labeled_cases = [case for case in cases if case.should_report is not None]
    candidate_thresholds = tuple(
        sorted({*thresholds, SEMANTIC_EVIDENCE_THRESHOLD})
    )
    metrics = [
        _calculate_metrics(labeled_cases, threshold)
        for threshold in candidate_thresholds
    ]
    current_metrics = next(
        metric
        for metric in metrics
        if metric.threshold == SEMANTIC_EVIDENCE_THRESHOLD
    )
    reviewed_live_cases = sum(case.source == "reviewed_live" for case in cases)
    warnings = []
    if reviewed_live_cases == 0:
        warnings.append(
            "The corpus contains synthetic baseline observations only. "
            "Do not enable semantic scoring until reviewed live similarities are added."
        )
    return SemanticCalibrationReport(
        fixture_path=str(fixture_path),
        total_cases=len(cases),
        labeled_cases=len(labeled_cases),
        reviewed_live_cases=reviewed_live_cases,
        synthetic_baseline_cases=sum(
            case.source == "synthetic_baseline" for case in cases
        ),
        pending_review_cases=sum(case.source == "pending_review" for case in cases),
        current_threshold=SEMANTIC_EVIDENCE_THRESHOLD,
        current_metrics=current_metrics,
        candidate_metrics=metrics,
        warnings=warnings,
    )


def _calculate_metrics(
    cases: list[SemanticCalibrationCase],
    threshold: float,
) -> SemanticThresholdMetrics:
    true_positive = false_positive = true_negative = false_negative = 0
    for case in cases:
        reported = case.cosine_similarity >= threshold
        if reported and case.should_report:
            true_positive += 1
        elif reported:
            false_positive += 1
        elif case.should_report:
            false_negative += 1
        else:
            true_negative += 1
    precision = _ratio(true_positive, true_positive + false_positive)
    recall = _ratio(true_positive, true_positive + false_negative)
    return SemanticThresholdMetrics(
        threshold=threshold,
        true_positive=true_positive,
        false_positive=false_positive,
        true_negative=true_negative,
        false_negative=false_negative,
        precision=precision,
        recall=recall,
        f1=_ratio(2 * precision * recall, precision + recall),
    )


def _ratio(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0
