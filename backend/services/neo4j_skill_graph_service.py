from collections import defaultdict

from database.neo4j import get_neo4j_driver
from services.related_skill_service import MAX_SUPPORT_PATH_LENGTH
from services.skill_graph_dataset_service import (
    SkillGraphRelationship,
    load_skill_graph_dataset,
    normalize_skill_term,
)

RELATIONSHIP_TYPES = {
    "evidence_for": "EVIDENCE_FOR",
    "related_to": "RELATED_TO",
    "prerequisite_for": "PREREQUISITE_FOR",
}


def initialize_skill_graph() -> dict:
    driver = get_neo4j_driver()
    dataset = load_skill_graph_dataset()
    _create_constraints(driver)
    skill_count = _seed_skills(driver, dataset.canonical_names)
    alias_count = _seed_aliases(driver, dataset.aliases)
    relationship_count = _seed_relationships(driver, dataset.relationships)
    role_count = _seed_roles(driver, dataset.roles)
    role_requirement_count = _seed_role_requirements(
        driver,
        dataset.role_requirements,
    )
    return {
        "source_files": list(dataset.source_files),
        "skill_count": skill_count,
        "alias_count": alias_count,
        "relationship_count": relationship_count,
        "role_count": role_count,
        "role_requirement_count": role_requirement_count,
    }


def find_skill_support_paths(
    resume_skill: str,
    requirement: str,
) -> list[dict]:
    return find_skill_support_paths_batch(
        resume_skills=[resume_skill],
        requirements=[requirement],
    )


def find_skill_support_paths_batch(
    resume_skills: list[str],
    requirements: list[str],
) -> list[dict]:
    if not resume_skills or not requirements:
        return []

    driver = get_neo4j_driver()
    records = driver.execute_query(
        """
        UNWIND $sources AS source_input
        MATCH (source:Skill {normalized_name: source_input.normalized_name})
        UNWIND $targets AS target_input
        MATCH (target:Skill {normalized_name: target_input.normalized_name})
        MATCH path = (source)-[relationships:EVIDENCE_FOR|RELATED_TO*1..2]->(target)
        WHERE length(path) < $max_path_length
        RETURN
            source_input.value AS resume_skill,
            target_input.value AS requirement,
            [node IN nodes(path) | node.canonical_name] AS nodes,
            [relationship IN relationships |
                {
                    relationship_type: relationship.relationship_type,
                    confidence: relationship.confidence
                }
            ] AS relationships
        ORDER BY
            resume_skill,
            requirement,
            reduce(score = 1.0, relationship IN relationships |
                score * relationship.confidence
            ) DESC,
            length(path) ASC
        """,
        sources=[
            {
                "value": skill,
                "normalized_name": normalize_skill_term(skill),
            }
            for skill in dict.fromkeys(resume_skills)
        ],
        targets=[
            {
                "value": requirement,
                "normalized_name": normalize_skill_term(requirement),
            }
            for requirement in dict.fromkeys(requirements)
        ],
        max_path_length=MAX_SUPPORT_PATH_LENGTH,
        routing_="r",
    ).records
    return [
        {
            "resume_skill": record["resume_skill"],
            "requirement": record["requirement"],
            "nodes": list(record["nodes"]),
            "relationships": [dict(item) for item in record["relationships"]],
        }
        for record in records
    ]


def _create_constraints(driver) -> None:
    statements = (
        """
        CREATE CONSTRAINT skill_normalized_name_unique IF NOT EXISTS
        FOR (skill:Skill)
        REQUIRE skill.normalized_name IS UNIQUE
        """,
        """
        CREATE CONSTRAINT skill_term_normalized_name_unique IF NOT EXISTS
        FOR (term:SkillTerm)
        REQUIRE term.normalized_name IS UNIQUE
        """,
        """
        CREATE CONSTRAINT role_normalized_name_unique IF NOT EXISTS
        FOR (role:Role)
        REQUIRE role.normalized_name IS UNIQUE
        """,
    )
    for statement in statements:
        driver.execute_query(statement)


def _seed_skills(driver, canonical_names: tuple[str, ...]) -> int:
    rows = [
        {
            "canonical_name": name,
            "normalized_name": normalize_skill_term(name),
        }
        for name in canonical_names
        if name.strip()
    ]
    driver.execute_query(
        """
        UNWIND $rows AS row
        MERGE (skill:Skill {normalized_name: row.normalized_name})
        ON CREATE SET skill.created_at = datetime()
        SET skill.canonical_name = row.canonical_name,
            skill.updated_at = datetime()
        """,
        rows=rows,
    )
    return len(rows)


def _seed_aliases(driver, aliases: dict[str, str]) -> int:
    rows = [
        {
            "display_name": alias,
            "normalized_name": normalize_skill_term(alias),
            "canonical_normalized_name": normalize_skill_term(canonical_name),
        }
        for alias, canonical_name in sorted(aliases.items())
        if normalize_skill_term(alias) != normalize_skill_term(canonical_name)
    ]
    driver.execute_query(
        """
        UNWIND $rows AS row
        MATCH (skill:Skill {normalized_name: row.canonical_normalized_name})
        MERGE (term:SkillTerm {normalized_name: row.normalized_name})
        ON CREATE SET term.created_at = datetime()
        SET term.display_name = row.display_name,
            term.updated_at = datetime()
        MERGE (term)-[relationship:ALIAS_OF]->(skill)
        ON CREATE SET relationship.created_at = datetime()
        SET relationship.relationship_type = 'alias_of',
            relationship.confidence = 1.0,
            relationship.source = 'dataset_json',
            relationship.updated_at = datetime()
        """,
        rows=rows,
    )
    return len(rows)


def _seed_relationships(
    driver,
    relationships: tuple[SkillGraphRelationship, ...],
) -> int:
    grouped: dict[str, list[SkillGraphRelationship]] = defaultdict(list)
    for relationship in relationships:
        grouped[relationship.relationship_type].append(relationship)

    total = 0
    for relationship_type, rules in grouped.items():
        neo4j_type = RELATIONSHIP_TYPES[relationship_type]
        rows = [
            {
                "source": normalize_skill_term(rule.source),
                "target": normalize_skill_term(rule.target),
                "confidence": rule.confidence,
                "domain": rule.domain,
            }
            for rule in rules
        ]
        driver.execute_query(
            f"""
            UNWIND $rows AS row
            MATCH (source:Skill {{normalized_name: row.source}})
            MATCH (target:Skill {{normalized_name: row.target}})
            MERGE (source)-[relationship:{neo4j_type}]->(target)
            ON CREATE SET relationship.created_at = datetime()
            SET relationship.relationship_type = $relationship_type,
                relationship.confidence = row.confidence,
                relationship.domain = row.domain,
                relationship.source = 'dataset_json',
                relationship.updated_at = datetime()
            """,
            rows=rows,
            relationship_type=relationship_type,
        )
        total += len(rows)
    return total


def _seed_roles(driver, roles) -> int:
    rows = [
        {
            "name": role.name,
            "normalized_name": normalize_skill_term(role.name),
            "aliases": list(role.aliases),
            "domain": role.domain,
            "description": role.description,
        }
        for role in roles
    ]
    driver.execute_query(
        """
        UNWIND $rows AS row
        MERGE (role:Role {normalized_name: row.normalized_name})
        ON CREATE SET role.created_at = datetime()
        SET role.name = row.name,
            role.aliases = row.aliases,
            role.domain = row.domain,
            role.description = row.description,
            role.source = 'dataset_json',
            role.updated_at = datetime()
        """,
        rows=rows,
    )
    return len(rows)


def _seed_role_requirements(driver, requirements) -> int:
    rows = [
        {
            "role": normalize_skill_term(requirement.role),
            "skill": normalize_skill_term(requirement.skill),
            "importance": requirement.importance,
            "confidence": requirement.confidence,
            "domain": requirement.domain,
        }
        for requirement in requirements
    ]
    driver.execute_query(
        """
        UNWIND $rows AS row
        MATCH (role:Role {normalized_name: row.role})
        MATCH (skill:Skill {normalized_name: row.skill})
        MERGE (role)-[relationship:REQUIRES]->(skill)
        ON CREATE SET relationship.created_at = datetime()
        SET relationship.importance = row.importance,
            relationship.confidence = row.confidence,
            relationship.domain = row.domain,
            relationship.source = 'dataset_json',
            relationship.updated_at = datetime()
        """,
        rows=rows,
    )
    return len(rows)


def find_prerequisite_paths_batch(
    current_skills: list[str],
    target_skills: list[str],
    max_edges: int = 4,
) -> list[dict]:
    if not current_skills or not target_skills:
        return []
    records = get_neo4j_driver().execute_query(
        """
        UNWIND $current_skills AS current_input
        MATCH (current:Skill {normalized_name: current_input.normalized_name})
        UNWIND $target_skills AS target_input
        MATCH (target:Skill {normalized_name: target_input.normalized_name})
        MATCH path = (current)-[relationships:PREREQUISITE_FOR*1..4]->(target)
        WHERE length(path) <= $max_edges
        RETURN
            current_input.value AS current_skill,
            target_input.value AS target_skill,
            [node IN nodes(path) | node.canonical_name] AS nodes,
            [relationship IN relationships |
                relationship.confidence
            ] AS confidences
        ORDER BY
            target_skill,
            length(path) ASC,
            reduce(score = 1.0, confidence IN confidences |
                score * confidence
            ) DESC
        """,
        current_skills=[
            {
                "value": skill,
                "normalized_name": normalize_skill_term(skill),
            }
            for skill in dict.fromkeys(current_skills)
        ],
        target_skills=[
            {
                "value": skill,
                "normalized_name": normalize_skill_term(skill),
            }
            for skill in dict.fromkeys(target_skills)
        ],
        max_edges=max_edges,
        routing_="r",
    ).records
    return [
        {
            "current_skill": record["current_skill"],
            "target_skill": record["target_skill"],
            "nodes": list(record["nodes"]),
            "confidences": list(record["confidences"]),
        }
        for record in records
    ]


def get_role_fit_from_graph(profile_skills: list[str]) -> list[dict]:
    records = get_neo4j_driver().execute_query(
        """
        MATCH (role:Role)-[requirement:REQUIRES]->(skill:Skill)
        WITH role, collect({
            skill: skill.canonical_name,
            normalized_name: skill.normalized_name,
            importance: requirement.importance,
            confidence: requirement.confidence
        }) AS requirements
        RETURN
            role.name AS role,
            role.description AS description,
            role.domain AS domain,
            requirements
        ORDER BY role.name
        """,
        routing_="r",
    ).records
    profile_keys = {normalize_skill_term(skill) for skill in profile_skills}
    results = []
    for record in records:
        requirements = [dict(item) for item in record["requirements"]]
        results.append(
            {
                "role": record["role"],
                "description": record["description"],
                "domain": record["domain"],
                "requirements": requirements,
                "matched_skills": [
                    item["skill"]
                    for item in requirements
                    if item["normalized_name"] in profile_keys
                ],
            }
        )
    return results
