from schemas.matching import (
    RelatedSkillEvidence,
    RelatedSkillRelationshipStep,
    ResumeSkillEvidence,
)
from services.neo4j_skill_graph_service import find_skill_support_paths_batch
from services.related_skill_service import (
    CuratedRelatedSkillEvidenceProvider,
    MAX_RELATED_SKILL_CREDIT_FACTOR,
    RELATED_PATH_DISTANCE_DECAY,
    RelatedSkillEvidenceProvider,
    normalize_requirement_name,
)


class Neo4jRelatedSkillEvidenceProvider:
    def find_evidence(
        self,
        resume_evidence: list[ResumeSkillEvidence],
        required_skills: list[str],
        preferred_skills: list[str],
        required_domain_concepts: list[str],
        preferred_domain_concepts: list[str],
    ) -> list[RelatedSkillEvidence]:
        requirement_groups = (
            ("required_skill", required_skills),
            ("preferred_skill", preferred_skills),
            ("required_domain_concept", required_domain_concepts),
            ("preferred_domain_concept", preferred_domain_concepts),
        )
        normalized_requirements = {
            requirement: normalize_requirement_name(requirement)
            for _, requirements in requirement_groups
            for requirement in requirements
        }
        paths = find_skill_support_paths_batch(
            resume_skills=[item.skill for item in resume_evidence],
            requirements=list(normalized_requirements.values()),
        )
        paths_by_pair: dict[tuple[str, str], list[dict]] = {}
        for path in paths:
            key = (path["resume_skill"], path["requirement"])
            paths_by_pair.setdefault(key, []).append(path)

        evidence = []
        for requirement_category, requirements in requirement_groups:
            for requirement in requirements:
                normalized_requirement = normalized_requirements[requirement]
                for resume_item in resume_evidence:
                    pair_paths = paths_by_pair.get(
                        (resume_item.skill, normalized_requirement),
                        [],
                    )
                    strongest = _strongest_path(pair_paths)
                    if not strongest:
                        continue
                    path_confidence = _path_confidence(strongest["relationships"])
                    distance_decay = RELATED_PATH_DISTANCE_DECAY ** max(
                        0,
                        len(strongest["relationships"]) - 1,
                    )
                    relationship_credit_factor = min(
                        MAX_RELATED_SKILL_CREDIT_FACTOR,
                        MAX_RELATED_SKILL_CREDIT_FACTOR
                        * path_confidence
                        * distance_decay,
                    )
                    steps = [
                        RelatedSkillRelationshipStep(
                            evidence=strongest["nodes"][index],
                            supported_requirement=strongest["nodes"][index + 1],
                            relationship_type=relationship["relationship_type"],
                            confidence=relationship["confidence"],
                        )
                        for index, relationship in enumerate(
                            strongest["relationships"]
                        )
                    ]
                    evidence.append(
                        RelatedSkillEvidence(
                            resume_skill=resume_item.skill,
                            resume_evidence=resume_item,
                            supported_requirement=requirement,
                            requirement_category=requirement_category,
                            relationship="supports",
                            source="neo4j",
                            support_path=strongest["nodes"],
                            relationship_path=steps,
                            path_distance=len(steps),
                            path_confidence=round(path_confidence, 4),
                            distance_decay=round(distance_decay, 4),
                            relationship_credit_factor=round(
                                relationship_credit_factor,
                                4,
                            ),
                            effective_credit_factor=round(
                                relationship_credit_factor
                                * resume_item.provenance_weight,
                                4,
                            ),
                        )
                    )
        return evidence


class FallbackRelatedSkillEvidenceProvider:
    def __init__(
        self,
        primary: RelatedSkillEvidenceProvider | None = None,
        fallback: RelatedSkillEvidenceProvider | None = None,
    ) -> None:
        self.primary = primary or Neo4jRelatedSkillEvidenceProvider()
        self.fallback = fallback or CuratedRelatedSkillEvidenceProvider()

    def find_evidence(
        self,
        resume_evidence: list[ResumeSkillEvidence],
        required_skills: list[str],
        preferred_skills: list[str],
        required_domain_concepts: list[str],
        preferred_domain_concepts: list[str],
    ) -> list[RelatedSkillEvidence]:
        arguments = {
            "resume_evidence": resume_evidence,
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "required_domain_concepts": required_domain_concepts,
            "preferred_domain_concepts": preferred_domain_concepts,
        }
        try:
            primary_evidence = self.primary.find_evidence(**arguments)
        except Exception:
            return self.fallback.find_evidence(**arguments)

        fallback_evidence = self.fallback.find_evidence(**arguments)
        primary_keys = {
            _evidence_key(item)
            for item in primary_evidence
        }
        return [
            *primary_evidence,
            *(
                item
                for item in fallback_evidence
                if _evidence_key(item) not in primary_keys
            ),
        ]


def _strongest_path(paths: list[dict]) -> dict | None:
    return max(
        paths,
        key=lambda path: (
            _path_confidence(path["relationships"])
            * RELATED_PATH_DISTANCE_DECAY
            ** max(0, len(path["relationships"]) - 1),
            -len(path["relationships"]),
        ),
        default=None,
    )


def _path_confidence(relationships: list[dict]) -> float:
    confidence = 1.0
    for relationship in relationships:
        confidence *= float(relationship["confidence"])
    return confidence


def _evidence_key(evidence: RelatedSkillEvidence) -> tuple[str, str, str]:
    return (
        evidence.resume_skill.casefold(),
        evidence.supported_requirement.casefold(),
        evidence.requirement_category,
    )
