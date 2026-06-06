import uuid
from collections import deque

from models.user import User
from schemas.matching import (
    MatchLearningPathItem,
    MatchLearningPathsResponse,
    MatchLearningPathStep,
    MatchPreviewResponse,
)
from services.match_analysis_service import _get_owned_match_analysis
from services.neo4j_skill_graph_service import (
    find_prerequisite_paths_batch,
    find_skill_support_paths_batch,
)
from services.skill_graph_dataset_service import (
    load_skill_graph_dataset,
    normalize_skill_term,
)

LEARNING_PATH_VERSION = "neo4j-match-learning-path-v2"
MAX_PATH_EDGES = 4


def get_match_learning_paths(
    database,
    user: User,
    analysis_id: uuid.UUID,
) -> MatchLearningPathsResponse:
    analysis = _get_owned_match_analysis(database, user, analysis_id)
    match = MatchPreviewResponse.model_validate(analysis.analysis_payload)
    existing_skills = match.resume_skills
    missing_required = match.technical_skills.required.missing_skills
    missing_preferred = match.technical_skills.preferred.missing_skills
    targets = [*missing_required, *missing_preferred]
    warnings = []

    prerequisite_source = "neo4j"
    try:
        prerequisite_paths = find_prerequisite_paths_batch(
            current_skills=existing_skills,
            target_skills=targets,
            max_edges=MAX_PATH_EDGES,
        )
    except Exception:
        prerequisite_source = "local_dataset"
        prerequisite_paths = _find_local_prerequisite_paths(
            existing_skills,
            targets,
        )
        warnings.append(
            "Neo4j learning paths were unavailable; local graph data was used."
        )

    support_source = "neo4j"
    try:
        support_paths = find_skill_support_paths_batch(
            existing_skills,
            targets,
        )
    except Exception:
        support_source = "local_dataset"
        support_paths = _find_local_support_paths(existing_skills, targets)
        warnings.append(
            "Neo4j foundation evidence was unavailable; local graph data was used."
        )

    strongest_prerequisite_by_target = {}
    for path in prerequisite_paths:
        target = normalize_skill_term(path["target_skill"])
        score = _path_confidence(path["confidences"])
        current = strongest_prerequisite_by_target.get(target)
        if current is None or (len(path["nodes"]), -score) < (
            len(current["nodes"]),
            -_path_confidence(current["confidences"]),
        ):
            strongest_prerequisite_by_target[target] = path

    strongest_support_by_target = {}
    for path in support_paths:
        target = normalize_skill_term(path["requirement"])
        score = _path_confidence(
            [
                relationship["confidence"]
                for relationship in path["relationships"]
            ]
        )
        current = strongest_support_by_target.get(target)
        if current is None or (
            score,
            -len(path["nodes"]),
        ) > (
            current["_score"],
            -len(current["nodes"]),
        ):
            strongest_support_by_target[target] = {**path, "_score": score}

    items = []
    for category, requirements in (
        ("required_skill", missing_required),
        ("preferred_skill", missing_preferred),
    ):
        for requirement in requirements:
            requirement_key = normalize_skill_term(requirement)
            prerequisite_path = strongest_prerequisite_by_target.get(
                requirement_key
            )
            support_path = strongest_support_by_target.get(requirement_key)
            items.append(
                _learning_path_item(
                    requirement=requirement,
                    category=category,
                    prerequisite_path=prerequisite_path,
                    prerequisite_source=prerequisite_source,
                    support_path=support_path,
                    support_source=support_source,
                )
            )

    return MatchLearningPathsResponse(
        analysis_id=analysis.id,
        resume_id=analysis.resume_id,
        internship_id=analysis.internship_input_id,
        version=LEARNING_PATH_VERSION,
        existing_skills=existing_skills,
        missing_required_skills=missing_required,
        missing_preferred_skills=missing_preferred,
        learning_paths=items,
        warnings=warnings,
    )


def _learning_path_item(
    requirement,
    category,
    prerequisite_path,
    prerequisite_source,
    support_path,
    support_source,
):
    if prerequisite_path:
        return MatchLearningPathItem(
            target_skill=requirement,
            requirement_category=category,
            priority="high" if category == "required_skill" else "medium",
            status="prerequisite_path_found",
            current_foundation=prerequisite_path["nodes"][0],
            steps=[
                MatchLearningPathStep(
                    order=index + 1,
                    skill=skill,
                    already_known=index == 0,
                )
                for index, skill in enumerate(prerequisite_path["nodes"])
            ],
            path_confidence=round(
                _path_confidence(prerequisite_path["confidences"]),
                4,
            ),
            source=prerequisite_source,
            relationship_types=["prerequisite_for"]
            * len(prerequisite_path["confidences"]),
            reason=(
                f"Build from {prerequisite_path['nodes'][0]} through the "
                f"reviewed prerequisite path to {requirement}."
            ),
        )
    if support_path:
        relationship_types = [
            relationship["relationship_type"]
            for relationship in support_path["relationships"]
        ]
        return MatchLearningPathItem(
            target_skill=requirement,
            requirement_category=category,
            priority="high" if category == "required_skill" else "medium",
            status="foundation_detected",
            current_foundation=support_path["nodes"][0],
            steps=[
                MatchLearningPathStep(
                    order=index + 1,
                    skill=skill,
                    already_known=index == 0,
                )
                for index, skill in enumerate(support_path["nodes"])
            ],
            path_confidence=round(support_path["_score"], 4),
            source=support_source,
            relationship_types=relationship_types,
            reason=(
                f"{support_path['nodes'][0]} provides reviewed related evidence "
                f"and a practical foundation for {requirement}."
            ),
        )
    else:
        return MatchLearningPathItem(
            target_skill=requirement,
            requirement_category=category,
            priority="high" if category == "required_skill" else "medium",
            status="direct_learning_required",
            current_foundation=None,
            steps=[
                MatchLearningPathStep(
                    order=1,
                    skill=requirement,
                    already_known=False,
                )
            ],
            path_confidence=None,
            source="none",
            relationship_types=[],
            reason=(
                "No reviewed prerequisite path currently connects the resume "
                "skills to this requirement."
            ),
        )


def _find_local_prerequisite_paths(
    current_skills: list[str],
    targets: list[str],
) -> list[dict]:
    adjacency = {}
    for relationship in load_skill_graph_dataset().relationships:
        if relationship.relationship_type != "prerequisite_for":
            continue
        adjacency.setdefault(normalize_skill_term(relationship.source), []).append(
            relationship
        )
    target_by_key = {
        normalize_skill_term(target): target
        for target in targets
    }
    results = []
    for current_skill in current_skills:
        queue = deque(
            [
                (
                    current_skill,
                    [current_skill],
                    [],
                )
            ]
        )
        visited_depth = {normalize_skill_term(current_skill): 0}
        while queue:
            current, nodes, confidences = queue.popleft()
            if len(confidences) >= MAX_PATH_EDGES:
                continue
            for relationship in adjacency.get(normalize_skill_term(current), []):
                target_key = normalize_skill_term(relationship.target)
                next_nodes = [*nodes, relationship.target]
                next_confidences = [*confidences, relationship.confidence]
                if target_key in target_by_key:
                    results.append(
                        {
                            "current_skill": current_skill,
                            "target_skill": target_by_key[target_key],
                            "nodes": next_nodes,
                            "confidences": next_confidences,
                        }
                    )
                depth = len(next_confidences)
                if depth < visited_depth.get(target_key, MAX_PATH_EDGES + 1):
                    visited_depth[target_key] = depth
                    queue.append(
                        (
                            relationship.target,
                            next_nodes,
                            next_confidences,
                        )
                    )
    return results


def _find_local_support_paths(
    current_skills: list[str],
    targets: list[str],
) -> list[dict]:
    from schemas.matching import ResumeSkillEvidence
    from services.related_skill_service import CuratedRelatedSkillEvidenceProvider

    evidence = CuratedRelatedSkillEvidenceProvider().find_evidence(
        resume_evidence=[
            ResumeSkillEvidence(
                skill=skill,
                section="skills_list",
                extraction_source="explicit",
                confidence=1,
                provenance_weight=1,
                context=None,
            )
            for skill in current_skills
        ],
        required_skills=targets,
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


def _path_confidence(confidences: list[float]) -> float:
    score = 1.0
    for confidence in confidences:
        score *= float(confidence)
    return score
