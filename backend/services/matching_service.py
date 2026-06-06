import uuid

from sqlalchemy.orm import Session

from models.user import User
from schemas.matching import (
    MatchPreviewResponse,
    MatchedSkillEvidence,
    RequirementCategoryScore,
    RelatedRequirementCredit,
    RelatedSkillEvidence,
    RelatedSkillScore,
    ResumeSkillEvidence,
    SemanticSkillScore,
    SkillSectionScore,
)
from services.ai.internship_schemas import ParsedInternship
from services.ai.schemas import ExtractedSkill, ParsedResume
from services.internship_profile_service import get_parsed_internship_requirements
from services.related_skill_service import (
    CuratedRelatedSkillEvidenceProvider,
    MAX_RELATED_SKILL_CREDIT_FACTOR,
    RELATED_PATH_DISTANCE_DECAY,
    RelatedSkillEvidenceProvider,
    normalize_requirement_name,
)
from database.neo4j import is_neo4j_configured
from services.neo4j_related_skill_service import FallbackRelatedSkillEvidenceProvider
from services.resume_profile_service import get_parsed_resume_profile
from services.resume_evidence_service import (
    collect_resume_skill_evidence,
    strongest_resume_evidence_by_skill,
    unique_resume_skill_names,
)
from services.skill_canonicalizer import (
    canonicalize_parsed_internship,
    canonicalize_parsed_resume,
)
from services.semantic_matching_service import (
    SEMANTIC_EVIDENCE_THRESHOLD,
    get_semantic_skill_score,
)

SCORE_VERSION = "separate-semantic-evidence-reporting-v6"
REQUIRED_SKILLS_WEIGHT = 0.8
PREFERRED_SKILLS_WEIGHT = 0.2


def get_match_preview(
    database: Session,
    user: User,
    resume_id: uuid.UUID,
    internship_id: uuid.UUID,
) -> MatchPreviewResponse:
    resume_profile = get_parsed_resume_profile(database, user, resume_id)
    internship_requirements = get_parsed_internship_requirements(
        database,
        user,
        internship_id,
    )
    semantic_skill_score = get_semantic_skill_score(
        database=database,
        resume_id=resume_id,
        internship_id=internship_id,
    )
    return calculate_skill_match(
        resume_id=resume_id,
        internship_id=internship_id,
        parsed_resume=resume_profile.parsed_resume,
        parsed_internship=internship_requirements.parsed_internship,
        related_skill_provider=(
            FallbackRelatedSkillEvidenceProvider()
            if is_neo4j_configured()
            else None
        ),
        semantic_skill_score=semantic_skill_score,
    )


def calculate_skill_match(
    resume_id: uuid.UUID,
    internship_id: uuid.UUID,
    parsed_resume: ParsedResume,
    parsed_internship: ParsedInternship,
    related_skill_provider: RelatedSkillEvidenceProvider | None = None,
    semantic_skill_score: SemanticSkillScore | None = None,
) -> MatchPreviewResponse:
    parsed_resume = canonicalize_parsed_resume(parsed_resume.model_copy(deep=True))
    parsed_internship = canonicalize_parsed_internship(
        parsed_internship.model_copy(deep=True)
    )

    resume_skill_evidence = collect_resume_skill_evidence(parsed_resume)
    resume_skills = unique_resume_skill_names(resume_skill_evidence)
    categorized_requirements = _categorize_requirements(parsed_internship)
    required_skills = categorized_requirements["required_skills"]
    preferred_skills = categorized_requirements["preferred_skills"]
    applied_required_weight, applied_preferred_weight = _get_applied_weights(
        required_skills,
        preferred_skills,
    )
    technical_skills = _build_category_score(
        resume_evidence=resume_skill_evidence,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        contributes_to_score=True,
        required_weight=applied_required_weight,
        preferred_weight=applied_preferred_weight,
    )
    exact_overlap_score = round(
        technical_skills.required.coverage_percentage
        * technical_skills.required.applied_weight
        + technical_skills.preferred.coverage_percentage
        * technical_skills.preferred.applied_weight,
        2,
    )
    domain_concepts = _build_category_score(
        resume_evidence=resume_skill_evidence,
        required_skills=categorized_requirements["required_domain_concepts"],
        preferred_skills=categorized_requirements["preferred_domain_concepts"],
        contributes_to_score=False,
    )
    soft_skills = _build_category_score(
        resume_evidence=resume_skill_evidence,
        required_skills=categorized_requirements["required_soft_skills"],
        preferred_skills=categorized_requirements["preferred_soft_skills"],
        contributes_to_score=False,
    )
    related_skill_provider = (
        related_skill_provider or CuratedRelatedSkillEvidenceProvider()
    )
    related_skill_evidence = related_skill_provider.find_evidence(
        resume_evidence=resume_skill_evidence,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        required_domain_concepts=categorized_requirements[
            "required_domain_concepts"
        ],
        preferred_domain_concepts=categorized_requirements[
            "preferred_domain_concepts"
        ],
    )
    related_skill_score = _calculate_related_skill_score(
        technical_skills=technical_skills,
        related_skill_evidence=related_skill_evidence,
    )
    overall_score = round(
        min(100.0, exact_overlap_score + related_skill_score.contribution_points),
        2,
    )
    semantic_skill_score = semantic_skill_score or _unavailable_semantic_score()

    warnings = []
    if not required_skills and not preferred_skills:
        warnings.append("The internship description did not identify concrete technical skills.")
    if not resume_skills:
        warnings.append("The resume did not identify any skills to compare.")
    broad_requirements = _find_broad_technical_requirements(
        [*required_skills, *preferred_skills]
    )
    if broad_requirements:
        warnings.append(
            "Some technical requirements are broad and may need manual review: "
            f"{', '.join(broad_requirements)}."
        )
    if (
        domain_concepts.required.missing_skills
        or domain_concepts.preferred.missing_skills
    ):
        warnings.append(
            "Domain concepts are shown separately. Curated relationships can explain "
            "supporting evidence, but domain concepts do not add numeric credit yet."
        )
    if soft_skills.required.missing_skills or soft_skills.preferred.missing_skills:
        warnings.append(
            "Soft skills are shown separately and do not affect the technical score."
        )

    return MatchPreviewResponse(
        score_version=SCORE_VERSION,
        resume_id=resume_id,
        internship_id=internship_id,
        overall_score=overall_score,
        exact_overlap_score=exact_overlap_score,
        related_skill_score=related_skill_score,
        semantic_skill_score=semantic_skill_score,
        resume_skills=resume_skills,
        resume_skill_evidence=resume_skill_evidence,
        technical_skills=technical_skills,
        domain_concepts=domain_concepts,
        soft_skills=soft_skills,
        related_skill_evidence=related_skill_evidence,
        warnings=warnings,
    )


def _unavailable_semantic_score() -> SemanticSkillScore:
    return SemanticSkillScore(
        available=False,
        contributes_to_score=False,
        model_name=None,
        reporting_threshold=SEMANTIC_EVIDENCE_THRESHOLD,
        evidence=[],
        warnings=[
            "Semantic evidence was not loaded for this deterministic calculation."
        ],
    )


def _calculate_related_skill_score(
    technical_skills: RequirementCategoryScore,
    related_skill_evidence: list[RelatedSkillEvidence],
) -> RelatedSkillScore:
    required_credits = _build_related_requirement_credits(
        related_skill_evidence=related_skill_evidence,
        requirement_category="required_skill",
        missing_skills=technical_skills.required.missing_skills,
        total_skill_count=_total_skill_count(technical_skills.required),
        applied_weight=technical_skills.required.applied_weight,
    )
    preferred_credits = _build_related_requirement_credits(
        related_skill_evidence=related_skill_evidence,
        requirement_category="preferred_skill",
        missing_skills=technical_skills.preferred.missing_skills,
        total_skill_count=_total_skill_count(technical_skills.preferred),
        applied_weight=technical_skills.preferred.applied_weight,
    )
    supported_required_skills = [credit.requirement for credit in required_credits]
    supported_preferred_skills = [credit.requirement for credit in preferred_credits]
    required_coverage = _coverage_percentage(
        supported_required_skills,
        _all_section_skills(technical_skills.required),
    )
    preferred_coverage = _coverage_percentage(
        supported_preferred_skills,
        _all_section_skills(technical_skills.preferred),
    )
    requirement_credits = [*required_credits, *preferred_credits]
    contribution_points = round(
        sum(credit.contribution_points for credit in requirement_credits),
        2,
    )
    return RelatedSkillScore(
        maximum_credit_factor=MAX_RELATED_SKILL_CREDIT_FACTOR,
        distance_decay_factor=RELATED_PATH_DISTANCE_DECAY,
        required_coverage_percentage=required_coverage,
        preferred_coverage_percentage=preferred_coverage,
        contribution_points=contribution_points,
        supported_required_skills=supported_required_skills,
        supported_preferred_skills=supported_preferred_skills,
        requirement_credits=requirement_credits,
    )


def _build_related_requirement_credits(
    related_skill_evidence: list[RelatedSkillEvidence],
    requirement_category: str,
    missing_skills: list[str],
    total_skill_count: int,
    applied_weight: float,
) -> list[RelatedRequirementCredit]:
    credits = []
    for missing_skill in missing_skills:
        matching_evidence = [
            evidence
            for evidence in related_skill_evidence
            if evidence.requirement_category == requirement_category
            and _comparison_key(evidence.supported_requirement)
            == _comparison_key(missing_skill)
        ]
        if not matching_evidence:
            continue
        strongest_evidence = max(
            matching_evidence,
            key=lambda evidence: (
                evidence.effective_credit_factor,
                -evidence.path_distance,
            ),
        )
        normal_requirement_points = (
            100.0 / total_skill_count * applied_weight if total_skill_count else 0.0
        )
        credits.append(
            RelatedRequirementCredit(
                requirement=missing_skill,
                requirement_category=requirement_category,
                credit_factor=strongest_evidence.effective_credit_factor,
                contribution_points=round(
                    normal_requirement_points
                    * strongest_evidence.effective_credit_factor,
                    2,
                ),
                strongest_evidence_path=strongest_evidence.support_path,
                strongest_resume_evidence=strongest_evidence.resume_evidence,
            )
        )
    return credits


def _all_section_skills(section: SkillSectionScore) -> list[str]:
    return [*section.matched_skills, *section.missing_skills]


def _total_skill_count(section: SkillSectionScore) -> int:
    return len(_all_section_skills(section))


def _coverage_percentage(supported_skills: list[str], all_skills: list[str]) -> float:
    return round(len(supported_skills) / len(all_skills) * 100, 2) if all_skills else 0.0


def _get_applied_weights(
    required_skills: list[str],
    preferred_skills: list[str],
) -> tuple[float, float]:
    if required_skills and preferred_skills:
        return REQUIRED_SKILLS_WEIGHT, PREFERRED_SKILLS_WEIGHT
    if required_skills:
        return 1.0, 0.0
    if preferred_skills:
        return 0.0, 1.0
    return 0.0, 0.0


def _build_section_score(
    resume_evidence: list[ResumeSkillEvidence],
    internship_skills: list[str],
    applied_weight: float,
) -> SkillSectionScore:
    resume_lookup = strongest_resume_evidence_by_skill(resume_evidence)
    matched_skills = [
        skill for skill in internship_skills if _comparison_key(skill) in resume_lookup
    ]
    missing_skills = [
        skill for skill in internship_skills if _comparison_key(skill) not in resume_lookup
    ]
    coverage_percentage = (
        round(len(matched_skills) / len(internship_skills) * 100, 2)
        if internship_skills
        else 0.0
    )
    return SkillSectionScore(
        applied_weight=applied_weight,
        coverage_percentage=coverage_percentage,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        matched_skill_evidence=[
            MatchedSkillEvidence(
                requirement=skill,
                strongest_evidence=resume_lookup[_comparison_key(skill)],
            )
            for skill in matched_skills
        ],
    )


def _build_category_score(
    resume_evidence: list[ResumeSkillEvidence],
    required_skills: list[str],
    preferred_skills: list[str],
    contributes_to_score: bool,
    required_weight: float = 0.0,
    preferred_weight: float = 0.0,
) -> RequirementCategoryScore:
    return RequirementCategoryScore(
        contributes_to_score=contributes_to_score,
        required=_build_section_score(
            resume_evidence,
            required_skills,
            required_weight,
        ),
        preferred=_build_section_score(
            resume_evidence,
            preferred_skills,
            preferred_weight,
        ),
    )


def _categorize_requirements(parsed_internship: ParsedInternship) -> dict[str, list[str]]:
    categories = {
        "required_skills": [],
        "preferred_skills": [],
        "required_domain_concepts": _normalize_domain_concepts(
            _unique_canonical_names(parsed_internship.required_domain_concepts)
        ),
        "preferred_domain_concepts": _normalize_domain_concepts(
            _unique_canonical_names(parsed_internship.preferred_domain_concepts)
        ),
        "required_soft_skills": _unique_canonical_names(
            parsed_internship.required_soft_skills
        ),
        "preferred_soft_skills": _unique_canonical_names(
            parsed_internship.preferred_soft_skills
        ),
    }
    for field in ("required_skills", "preferred_skills"):
        for name in _unique_canonical_names(getattr(parsed_internship, field)):
            destination = _legacy_requirement_category(name, field)
            categories[destination].append(name)
    for field in ("required_domain_concepts", "preferred_domain_concepts"):
        categories[field] = _normalize_domain_concepts(categories[field])
    return {field: _deduplicate(names) for field, names in categories.items()}


def _normalize_domain_concepts(names: list[str]) -> list[str]:
    return [normalize_requirement_name(name) for name in names]


def _find_broad_technical_requirements(names: list[str]) -> list[str]:
    return [
        name for name in names if _comparison_key(name) in BROAD_TECHNICAL_REQUIREMENTS
    ]


def _legacy_requirement_category(name: str, importance_field: str) -> str:
    suffix = "required" if importance_field == "required_skills" else "preferred"
    comparison_key = _comparison_key(name)
    if comparison_key in LEGACY_SOFT_SKILLS:
        return f"{suffix}_soft_skills"
    if comparison_key in LEGACY_DOMAIN_CONCEPTS:
        return f"{suffix}_domain_concepts"
    return importance_field


def _unique_canonical_names(skills: list[ExtractedSkill]) -> list[str]:
    unique_names = {}
    for skill in skills:
        name = (skill.canonical_name or skill.name).strip()
        if name:
            unique_names.setdefault(_comparison_key(name), name)
    return list(unique_names.values())


def _deduplicate(names: list[str]) -> list[str]:
    unique_names = {}
    for name in names:
        unique_names.setdefault(_comparison_key(name), name)
    return list(unique_names.values())


def _comparison_key(skill_name: str) -> str:
    return skill_name.casefold()


# Older internship-parser-v1 documents mixed broad concepts and soft skills into
# technical skill lists. Keep previews honest until those documents are reparsed.
LEGACY_DOMAIN_CONCEPTS = {
    "network security principles",
    "qa processes",
    "security concepts",
    "web technologies",
}
LEGACY_SOFT_SKILLS = {
    "analytical skills",
    "attention to detail",
    "communication",
    "communication skills",
    "customer service",
    "customer support",
    "problem solving",
    "teamwork",
}
BROAD_TECHNICAL_REQUIREMENTS = {
    "troubleshooting",
}
