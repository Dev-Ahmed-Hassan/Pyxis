from fastapi import HTTPException, status

from schemas.career import (
    GraphCareerLearningStep,
    GraphCareerPath,
    GraphCareerRecommendationsResponse,
    GraphCareerRelatedSupport,
    GraphCareerSkillGap,
)
from services.graph_learning_path_service import _find_local_prerequisite_paths
from services.neo4j_skill_graph_service import (
    find_skill_support_paths_batch,
    find_prerequisite_paths_batch,
    get_role_fit_from_graph,
)
from services.related_skill_service import (
    MAX_RELATED_SKILL_CREDIT_FACTOR,
    RELATED_PATH_DISTANCE_DECAY,
)
from services.skill_graph_dataset_service import (
    load_skill_graph_dataset,
    normalize_skill_term,
)
from services.user_profile_facts_service import get_user_profile_facts

GRAPH_CAREER_VERSION = "profile-skill-graph-career-v2"
DEFAULT_LIMIT = 8


def get_graph_career_recommendations(
    database,
    user,
    limit: int = DEFAULT_LIMIT,
) -> GraphCareerRecommendationsResponse:
    profile = get_user_profile_facts(database, user)
    profile_skills = [item.canonical_name for item in profile.skill_inventory]
    if not profile_skills:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile facts are empty. Refresh profile facts after at least one resume is ready.",
        )
    warnings = []
    source = "neo4j"
    try:
        roles = get_role_fit_from_graph(profile_skills)
        if not roles:
            source = "local_dataset"
            roles = _local_role_fits(profile_skills)
            warnings.append(
                "Neo4j has no seeded roles; local graph data was used."
            )
    except Exception:
        source = "local_dataset"
        roles = _local_role_fits(profile_skills)
        warnings.append(
            "Neo4j role recommendations were unavailable; local graph data was used."
        )

    all_requirements = list(
        dict.fromkeys(
            requirement["skill"]
            for role in roles
            for requirement in role["requirements"]
        )
    )
    try:
        related_paths = find_skill_support_paths_batch(
            profile_skills,
            all_requirements,
        )
    except Exception:
        related_paths = _find_local_related_paths(
            profile_skills,
            all_requirements,
        )
        if source == "neo4j":
            warnings.append(
                "Neo4j role data was available, but related-skill support used local graph data."
            )
    related_support = _strongest_related_support(related_paths)

    ranked = sorted(
        (
            _score_role(role, profile_skills, related_support)
            for role in roles
        ),
        key=lambda item: (
            -_fit_level_rank(item["fit_level"]),
            -item["fit_score"],
            len(item["missing_required"]),
            item["role"].casefold(),
        ),
    )[:limit]

    missing_targets = list(
        dict.fromkeys(
            skill
            for role in ranked
            for skill in [*role["missing_required"], *role["missing_preferred"]]
        )
    )
    try:
        paths = find_prerequisite_paths_batch(profile_skills, missing_targets)
        path_source = "neo4j"
    except Exception:
        paths = _find_local_prerequisite_paths(profile_skills, missing_targets)
        path_source = "local_dataset"
    paths_by_target = _strongest_paths_by_target(paths)

    recommendations = []
    for role in ranked:
        gaps = []
        importance_by_skill = {
            item["skill"]: item["importance"]
            for item in role["requirements"]
        }
        for skill in [*role["missing_required"], *role["missing_preferred"]]:
            path = paths_by_target.get(normalize_skill_term(skill))
            gaps.append(
                GraphCareerSkillGap(
                    skill=skill,
                    importance=importance_by_skill[skill],
                    path_from_skill=path["nodes"][0] if path else None,
                    learning_steps=[
                        GraphCareerLearningStep(
                            order=index + 1,
                            skill=node,
                            already_known=index == 0,
                        )
                        for index, node in enumerate(path["nodes"])
                    ]
                    if path
                    else [
                        GraphCareerLearningStep(
                            order=1,
                            skill=skill,
                            already_known=False,
                        )
                    ],
                )
            )
        recommendations.append(
            GraphCareerPath(
                role=role["role"],
                description=role["description"],
                domain=role["domain"],
                fit_score=role["fit_score"],
                fit_level=role["fit_level"],
                exact_required_coverage=role["exact_required_coverage"],
                matched_skills=role["matched_skills"],
                related_skill_support=[
                    GraphCareerRelatedSupport(
                        requirement=item["requirement"],
                        supporting_skill=item["supporting_skill"],
                        support_path=item["support_path"],
                        credit_factor=item["credit_factor"],
                    )
                    for item in role["related_skill_support"]
                ],
                missing_required_skills=role["missing_required"],
                missing_preferred_skills=role["missing_preferred"],
                learning_gaps=gaps,
            )
        )

    if path_source != source:
        warnings.append(
            f"Role ranking used {source}; learning paths used {path_source}."
        )
    return GraphCareerRecommendationsResponse(
        version=GRAPH_CAREER_VERSION,
        user_id=user.id,
        profile_skill_count=len(profile_skills),
        graph_source=source,
        recommendations=recommendations,
        warnings=warnings,
    )


def _local_role_fits(profile_skills):
    dataset = load_skill_graph_dataset()
    requirements_by_role = {}
    for requirement in dataset.role_requirements:
        requirements_by_role.setdefault(requirement.role, []).append(
            {
                "skill": requirement.skill,
                "normalized_name": normalize_skill_term(requirement.skill),
                "importance": requirement.importance,
                "confidence": requirement.confidence,
            }
        )
    profile_keys = {normalize_skill_term(skill) for skill in profile_skills}
    return [
        {
            "role": role.name,
            "description": role.description,
            "domain": role.domain,
            "requirements": requirements_by_role.get(role.name, []),
            "matched_skills": [
                item["skill"]
                for item in requirements_by_role.get(role.name, [])
                if item["normalized_name"] in profile_keys
            ],
        }
        for role in dataset.roles
    ]


def _score_role(role, profile_skills, related_support):
    profile_keys = {normalize_skill_term(skill) for skill in profile_skills}
    required = [
        item for item in role["requirements"] if item["importance"] == "required"
    ]
    preferred = [
        item for item in role["requirements"] if item["importance"] == "preferred"
    ]
    required_total = sum(item["confidence"] for item in required)
    preferred_total = sum(item["confidence"] for item in preferred)
    required_exact = [
        item for item in required if item["normalized_name"] in profile_keys
    ]
    preferred_exact = [
        item for item in preferred if item["normalized_name"] in profile_keys
    ]
    required_matched = sum(item["confidence"] for item in required_exact)
    preferred_matched = sum(item["confidence"] for item in preferred_exact)
    role_related_support = []
    for item in role["requirements"]:
        if item["normalized_name"] in profile_keys:
            continue
        support = related_support.get(item["normalized_name"])
        if not support:
            continue
        contribution = item["confidence"] * support["credit_factor"]
        if item["importance"] == "required":
            required_matched += contribution
        else:
            preferred_matched += contribution
        role_related_support.append(
            {
                "requirement": item["skill"],
                **support,
            }
        )
    required_score = required_matched / required_total if required_total else 1
    preferred_score = preferred_matched / preferred_total if preferred_total else 1
    fit_score = round((required_score * 0.8 + preferred_score * 0.2) * 100, 2)
    exact_required_coverage = (
        len(required_exact) / len(required) if required else 1
    )
    exact_required_percentage = round(exact_required_coverage * 100, 2)
    fit_level = _fit_level(fit_score, exact_required_percentage)
    return {
        **role,
        "fit_score": fit_score,
        "fit_level": fit_level,
        "exact_required_coverage": exact_required_percentage,
        "related_skill_support": role_related_support,
        "matched_skills": [
            item["skill"]
            for item in role["requirements"]
            if item["normalized_name"] in profile_keys
        ],
        "missing_required": [
            item["skill"]
            for item in required
            if item["normalized_name"] not in profile_keys
        ],
        "missing_preferred": [
            item["skill"]
            for item in preferred
            if item["normalized_name"] not in profile_keys
        ],
    }


def _strongest_paths_by_target(paths):
    strongest = {}
    for path in paths:
        key = normalize_skill_term(path["target_skill"])
        score = 1.0
        for confidence in path["confidences"]:
            score *= float(confidence)
        current = strongest.get(key)
        if current is None or (len(path["nodes"]), -score) < (
            len(current["nodes"]),
            -current["_score"],
        ):
            strongest[key] = {**path, "_score": score}
    return strongest


def _strongest_related_support(paths):
    strongest = {}
    for path in paths:
        target_key = normalize_skill_term(path["requirement"])
        confidences = [
            float(item["confidence"])
            for item in path["relationships"]
        ]
        confidence = 1.0
        for value in confidences:
            confidence *= value
        distance_decay = RELATED_PATH_DISTANCE_DECAY ** max(
            0,
            len(confidences) - 1,
        )
        credit_factor = round(
            min(
                MAX_RELATED_SKILL_CREDIT_FACTOR,
                MAX_RELATED_SKILL_CREDIT_FACTOR
                * confidence
                * distance_decay,
            ),
            4,
        )
        candidate = {
            "supporting_skill": path["resume_skill"],
            "support_path": path["nodes"],
            "credit_factor": credit_factor,
        }
        current = strongest.get(target_key)
        if current is None or (
            candidate["credit_factor"],
            -len(candidate["support_path"]),
        ) > (
            current["credit_factor"],
            -len(current["support_path"]),
        ):
            strongest[target_key] = candidate
    return strongest


def _find_local_related_paths(profile_skills, requirements):
    from services.related_skill_service import CuratedRelatedSkillEvidenceProvider
    from schemas.matching import ResumeSkillEvidence

    provider = CuratedRelatedSkillEvidenceProvider()
    evidence = provider.find_evidence(
        resume_evidence=[
            ResumeSkillEvidence(
                skill=skill,
                section="skills_list",
                extraction_source="explicit",
                confidence=1,
                provenance_weight=1,
                context=None,
            )
            for skill in profile_skills
        ],
        required_skills=requirements,
        preferred_skills=[],
        required_domain_concepts=[],
        preferred_domain_concepts=[],
    )
    return [
        {
            "resume_skill": item.resume_skill,
            "requirement": item.supported_requirement,
            "nodes": item.support_path,
            "relationships": [
                {
                    "relationship_type": step.relationship_type,
                    "confidence": step.confidence,
                }
                for step in item.relationship_path
            ],
        }
        for item in evidence
    ]


def _fit_level(score, exact_required_coverage):
    if score >= 75 and exact_required_coverage >= 80:
        return "strong"
    if score >= 55 and exact_required_coverage >= 70:
        return "good"
    if score >= 25:
        return "emerging"
    return "explore_later"


def _fit_level_rank(fit_level):
    return {
        "strong": 3,
        "good": 2,
        "emerging": 1,
        "explore_later": 0,
    }[fit_level]
