import json
import uuid
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from schemas.matching import MatchPreviewResponse
from services.ai.internship_schemas import ParsedInternship
from services.ai.schemas import ParsedResume
from services.matching_service import calculate_skill_match

DEFAULT_FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent
    / "tests"
    / "fixtures"
    / "matching_engine_cases.json"
)


class ScoreRange(BaseModel):
    minimum: float = Field(ge=0.0, le=100.0)
    maximum: float = Field(ge=0.0, le=100.0)


class EvidencePathExpectation(BaseModel):
    supported_requirement: str
    support_path: list[str]


class MatchingEvaluationExpectation(BaseModel):
    overall_score: ScoreRange
    exact_overlap_score: ScoreRange
    supported_required_skills: list[str] = Field(default_factory=list)
    supported_preferred_skills: list[str] = Field(default_factory=list)
    evidence_paths: list[EvidencePathExpectation] = Field(default_factory=list)
    warning_substrings: list[str] = Field(default_factory=list)


class FixtureSkill(BaseModel):
    name: str
    extraction_source: Literal["explicit", "inferred", "manual"] = "explicit"
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


class FixtureSkillGroup(BaseModel):
    context: str
    skills: list[str | FixtureSkill]


class FixtureCertification(BaseModel):
    name: str
    issuer: str | None = None
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


class MatchingEvaluationCase(BaseModel):
    id: str
    domain: str
    description: str
    resume_skills: list[str | FixtureSkill]
    resume_projects: list[FixtureSkillGroup] = Field(default_factory=list)
    resume_experience: list[FixtureSkillGroup] = Field(default_factory=list)
    resume_certifications: list[FixtureCertification] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    required_domain_concepts: list[str] = Field(default_factory=list)
    preferred_domain_concepts: list[str] = Field(default_factory=list)
    required_soft_skills: list[str] = Field(default_factory=list)
    preferred_soft_skills: list[str] = Field(default_factory=list)
    expected: MatchingEvaluationExpectation


class MatchingEvaluationResult(BaseModel):
    case_id: str
    domain: str
    passed: bool
    issues: list[str]
    match: MatchPreviewResponse


class MatchingEvaluationReport(BaseModel):
    fixture_path: str
    score_version: str | None
    total_cases: int
    passed_cases: int
    failed_cases: int
    results: list[MatchingEvaluationResult]


def load_evaluation_cases(
    fixture_path: Path = DEFAULT_FIXTURE_PATH,
) -> list[MatchingEvaluationCase]:
    fixture_data = json.loads(fixture_path.read_text(encoding="utf-8"))
    return [
        MatchingEvaluationCase.model_validate(case_data)
        for case_data in fixture_data["cases"]
    ]


def run_matching_evaluation(
    fixture_path: Path = DEFAULT_FIXTURE_PATH,
) -> MatchingEvaluationReport:
    results = [_evaluate_case(case) for case in load_evaluation_cases(fixture_path)]
    score_versions = {result.match.score_version for result in results}
    return MatchingEvaluationReport(
        fixture_path=str(fixture_path),
        score_version=score_versions.pop() if len(score_versions) == 1 else None,
        total_cases=len(results),
        passed_cases=sum(result.passed for result in results),
        failed_cases=sum(not result.passed for result in results),
        results=results,
    )


def _evaluate_case(case: MatchingEvaluationCase) -> MatchingEvaluationResult:
    match = calculate_skill_match(
        resume_id=uuid.uuid5(uuid.NAMESPACE_URL, f"pyxis:resume:{case.id}"),
        internship_id=uuid.uuid5(uuid.NAMESPACE_URL, f"pyxis:internship:{case.id}"),
        parsed_resume=_parsed_resume(case),
        parsed_internship=_parsed_internship(case),
    )
    issues = _find_issues(case.expected, match)
    return MatchingEvaluationResult(
        case_id=case.id,
        domain=case.domain,
        passed=not issues,
        issues=issues,
        match=match,
    )


def _find_issues(
    expected: MatchingEvaluationExpectation,
    match: MatchPreviewResponse,
) -> list[str]:
    issues = []
    _check_score_range("overall_score", expected.overall_score, match.overall_score, issues)
    _check_score_range(
        "exact_overlap_score",
        expected.exact_overlap_score,
        match.exact_overlap_score,
        issues,
    )
    _check_list(
        "supported_required_skills",
        expected.supported_required_skills,
        match.related_skill_score.supported_required_skills,
        issues,
    )
    _check_list(
        "supported_preferred_skills",
        expected.supported_preferred_skills,
        match.related_skill_score.supported_preferred_skills,
        issues,
    )
    actual_paths = {
        (evidence.supported_requirement, tuple(evidence.support_path))
        for evidence in match.related_skill_evidence
    }
    for expected_path in expected.evidence_paths:
        path_key = (
            expected_path.supported_requirement,
            tuple(expected_path.support_path),
        )
        if path_key not in actual_paths:
            issues.append(
                "missing evidence path: "
                f"{' -> '.join(expected_path.support_path)} "
                f"for {expected_path.supported_requirement}"
            )
    for warning_substring in expected.warning_substrings:
        if not any(warning_substring in warning for warning in match.warnings):
            issues.append(f"missing warning containing: {warning_substring}")
    return issues


def _check_score_range(
    field: str,
    expected: ScoreRange,
    actual: float,
    issues: list[str],
) -> None:
    if not expected.minimum <= actual <= expected.maximum:
        issues.append(
            f"{field} expected {expected.minimum}-{expected.maximum}, received {actual}"
        )


def _check_list(
    field: str,
    expected: list[str],
    actual: list[str],
    issues: list[str],
) -> None:
    if expected != actual:
        issues.append(f"{field} expected {expected}, received {actual}")


def _parsed_resume(case: MatchingEvaluationCase) -> ParsedResume:
    return ParsedResume.model_validate(
        {
            "full_name": _text("Evaluation Candidate"),
            "email": _text("candidate@example.com"),
            "phone": _text(),
            "location": _text(),
            "summary": _text(),
            "skills": [_skill(skill) for skill in case.resume_skills],
            "experience": [
                {
                    "company": group.context,
                    "role": "Evaluation Role",
                    "start_date": None,
                    "end_date": None,
                    "description": [],
                    "skills": [_skill(skill) for skill in group.skills],
                    "confidence": 0.9,
                    "evidence": group.context,
                }
                for group in case.resume_experience
            ],
            "projects": [
                {
                    "name": group.context,
                    "description": [],
                    "skills": [_skill(skill) for skill in group.skills],
                    "confidence": 0.9,
                    "evidence": group.context,
                }
                for group in case.resume_projects
            ],
            "education": [],
            "certifications": [
                certification.model_dump()
                | {"evidence": certification.name}
                for certification in case.resume_certifications
            ],
        }
    )


def _parsed_internship(case: MatchingEvaluationCase) -> ParsedInternship:
    return ParsedInternship.model_validate(
        {
            "title": _text("Evaluation Internship"),
            "company": _text("Evaluation Company"),
            "location": _text(),
            "experience_level": _text(),
            "required_skills": [_skill(skill) for skill in case.required_skills],
            "preferred_skills": [_skill(skill) for skill in case.preferred_skills],
            "required_domain_concepts": [
                _skill(skill) for skill in case.required_domain_concepts
            ],
            "preferred_domain_concepts": [
                _skill(skill) for skill in case.preferred_domain_concepts
            ],
            "required_soft_skills": [
                _skill(skill) for skill in case.required_soft_skills
            ],
            "preferred_soft_skills": [
                _skill(skill) for skill in case.preferred_soft_skills
            ],
            "responsibilities": [],
            "qualifications": [],
        }
    )


def _text(value: str | None = None) -> dict:
    return {
        "value": value,
        "confidence": 0.9 if value else 0.0,
        "evidence": value,
    }


def _skill(skill: str | FixtureSkill) -> dict:
    if isinstance(skill, str):
        skill = FixtureSkill(name=skill)
    return {
        "name": skill.name,
        "confidence": skill.confidence,
        "evidence": skill.name,
        "source": skill.extraction_source,
    }
