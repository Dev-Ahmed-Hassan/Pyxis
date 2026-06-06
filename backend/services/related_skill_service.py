from collections import deque
from dataclasses import dataclass
from typing import Literal, Protocol

from schemas.matching import (
    RelatedSkillEvidence,
    RelatedSkillRelationshipStep,
    ResumeSkillEvidence,
)
from services.skill_graph_dataset_service import load_skill_graph_dataset

RelationshipType = Literal[
    "alias_of",
    "evidence_for",
    "related_to",
    "prerequisite_for",
]


@dataclass(frozen=True)
class RelatedSkillRule:
    evidence: str
    supported_requirement: str
    relationship_type: RelationshipType
    confidence: float


@dataclass(frozen=True)
class SupportPath:
    nodes: list[str]
    steps: list[RelatedSkillRelationshipStep]
    confidence: float
    distance_decay: float
    effective_credit_factor: float


class RelatedSkillEvidenceProvider(Protocol):
    def find_evidence(
        self,
        resume_evidence: list[ResumeSkillEvidence],
        required_skills: list[str],
        preferred_skills: list[str],
        required_domain_concepts: list[str],
        preferred_domain_concepts: list[str],
    ) -> list[RelatedSkillEvidence]: ...


class CuratedRelatedSkillEvidenceProvider:
    def __init__(self, rules: tuple[RelatedSkillRule, ...] | None = None) -> None:
        self.rules = rules or CURATED_RELATED_SKILL_RULES

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
        evidence = []
        for requirement_category, requirements in requirement_groups:
            for requirement in requirements:
                for resume_item in resume_evidence:
                    support_path = self._find_support_path(
                        resume_item.skill,
                        requirement,
                    )
                    if support_path:
                        evidence.append(
                            RelatedSkillEvidence(
                                resume_skill=resume_item.skill,
                                resume_evidence=resume_item,
                                supported_requirement=requirement,
                                requirement_category=requirement_category,
                                relationship="supports",
                                source="curated_rule",
                                support_path=support_path.nodes,
                                relationship_path=support_path.steps,
                                path_distance=len(support_path.steps),
                                path_confidence=support_path.confidence,
                                distance_decay=support_path.distance_decay,
                                relationship_credit_factor=(
                                    support_path.effective_credit_factor
                                ),
                                effective_credit_factor=round(
                                    support_path.effective_credit_factor
                                    * resume_item.provenance_weight,
                                    4,
                                ),
                            )
                        )
        return evidence

    def _find_support_path(
        self,
        resume_skill: str,
        requirement: str,
    ) -> SupportPath | None:
        target_key = _comparison_key(normalize_requirement_name(requirement))
        queue = deque([(resume_skill, [resume_skill], [])])
        candidates = []
        while queue:
            current_term, nodes, steps = queue.popleft()
            if len(nodes) > MAX_SUPPORT_PATH_LENGTH:
                continue
            for rule in self.rules:
                if _comparison_key(rule.evidence) != _comparison_key(current_term):
                    continue
                if rule.relationship_type not in SCORING_RELATIONSHIP_TYPES:
                    continue
                supported_term = rule.supported_requirement
                supported_key = _comparison_key(supported_term)
                next_nodes = [*nodes, supported_term]
                if len(next_nodes) > MAX_SUPPORT_PATH_LENGTH:
                    continue
                next_steps = [
                    *steps,
                    RelatedSkillRelationshipStep(
                        evidence=rule.evidence,
                        supported_requirement=rule.supported_requirement,
                        relationship_type=rule.relationship_type,
                        confidence=rule.confidence,
                    ),
                ]
                if supported_key == target_key:
                    candidates.append(_build_support_path(next_nodes, next_steps))
                elif supported_key not in {_comparison_key(node) for node in nodes}:
                    queue.append((supported_term, next_nodes, next_steps))
        return max(
            candidates,
            key=lambda path: (path.effective_credit_factor, -len(path.steps)),
            default=None,
        )


def _comparison_key(value: str) -> str:
    return value.casefold()


def normalize_requirement_name(value: str) -> str:
    return REQUIREMENT_ALIASES.get(_comparison_key(value), value)


MAX_SUPPORT_PATH_LENGTH = 3
MAX_RELATED_SKILL_CREDIT_FACTOR = 0.5
RELATED_PATH_DISTANCE_DECAY = 0.85
SCORING_RELATIONSHIP_TYPES = {"evidence_for", "related_to"}
REQUIREMENT_ALIASES = {
    "network security principles": "Network Security",
    "security concepts": "Cybersecurity Fundamentals",
}
CURATED_RELATED_SKILL_RULES = tuple(
    RelatedSkillRule(
        relationship.source,
        relationship.target,
        relationship.relationship_type,
        relationship.confidence,
    )
    for relationship in load_skill_graph_dataset().relationships
)


def _build_support_path(
    nodes: list[str],
    steps: list[RelatedSkillRelationshipStep],
) -> SupportPath:
    path_confidence = 1.0
    for step in steps:
        path_confidence *= step.confidence
    distance_decay = RELATED_PATH_DISTANCE_DECAY ** max(0, len(steps) - 1)
    return SupportPath(
        nodes=nodes,
        steps=steps,
        confidence=round(path_confidence, 4),
        distance_decay=round(distance_decay, 4),
        effective_credit_factor=round(
            MAX_RELATED_SKILL_CREDIT_FACTOR * path_confidence * distance_decay,
            4,
        ),
    )
