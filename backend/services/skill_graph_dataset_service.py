import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

RelationshipType = Literal[
    "evidence_for",
    "related_to",
    "prerequisite_for",
]
RoleRequirementImportance = Literal["required", "preferred"]

ALLOWED_RELATIONSHIP_TYPES = {
    "evidence_for",
    "related_to",
    "prerequisite_for",
}
DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "data" / "skill_graph"


class SkillGraphDatasetError(ValueError):
    pass


@dataclass(frozen=True)
class SkillGraphRelationship:
    source: str
    target: str
    relationship_type: RelationshipType
    confidence: float
    domain: str


@dataclass(frozen=True)
class SkillGraphRole:
    name: str
    aliases: tuple[str, ...]
    domain: str
    description: str


@dataclass(frozen=True)
class SkillGraphRoleRequirement:
    role: str
    skill: str
    importance: RoleRequirementImportance
    confidence: float
    domain: str


@dataclass(frozen=True)
class SkillGraphDataset:
    canonical_names: tuple[str, ...]
    aliases: dict[str, str]
    relationships: tuple[SkillGraphRelationship, ...]
    roles: tuple[SkillGraphRole, ...]
    role_requirements: tuple[SkillGraphRoleRequirement, ...]
    source_files: tuple[str, ...]


@lru_cache(maxsize=1)
def load_skill_graph_dataset() -> SkillGraphDataset:
    files = sorted(DATA_DIRECTORY.glob("*.json"))
    if not files:
        raise SkillGraphDatasetError(
            f"No skill graph datasets were found in {DATA_DIRECTORY}"
        )

    canonical_by_key: dict[str, str] = {}
    canonical_owner: dict[str, str] = {}
    aliases: dict[str, str] = {}
    alias_owner: dict[str, str] = {}
    relationships: list[SkillGraphRelationship] = []
    relationship_keys: set[tuple[str, str, str]] = set()
    roles: list[SkillGraphRole] = []
    role_by_key: dict[str, str] = {}
    role_requirements: list[SkillGraphRoleRequirement] = []
    role_requirement_keys: set[tuple[str, str]] = set()

    payloads = []
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise SkillGraphDatasetError(f"{path.name}: invalid JSON: {error}") from error
        _require_type(payload, dict, path, "root")
        if payload.get("schema_version") != 1:
            raise SkillGraphDatasetError(
                f"{path.name}: schema_version must be 1"
            )
        domain = _required_text(payload, "domain", path)
        skills = payload.get("skills")
        file_relationships = payload.get("relationships")
        file_roles = payload.get("roles", [])
        file_role_requirements = payload.get("role_requirements", [])
        _require_type(skills, list, path, "skills")
        _require_type(file_relationships, list, path, "relationships")
        _require_type(file_roles, list, path, "roles")
        _require_type(file_role_requirements, list, path, "role_requirements")
        payloads.append(
            (
                path,
                domain,
                skills,
                file_relationships,
                file_roles,
                file_role_requirements,
            )
        )

        for index, skill in enumerate(skills):
            _require_type(skill, dict, path, f"skills[{index}]")
            canonical_name = _required_text(
                skill,
                "canonical_name",
                path,
                f"skills[{index}]",
            )
            canonical_key = normalize_skill_term(canonical_name)
            previous_owner = canonical_owner.get(canonical_key)
            if previous_owner:
                raise SkillGraphDatasetError(
                    f"{path.name}: duplicate canonical skill {canonical_name!r}; "
                    f"already defined in {previous_owner}"
                )
            canonical_owner[canonical_key] = path.name
            canonical_by_key[canonical_key] = canonical_name

            skill_aliases = skill.get("aliases", [])
            _require_type(skill_aliases, list, path, f"skills[{index}].aliases")
            _register_alias(
                aliases,
                alias_owner,
                canonical_name,
                canonical_name,
                path.name,
            )
            for alias_index, alias in enumerate(skill_aliases):
                if not isinstance(alias, str) or not alias.strip():
                    raise SkillGraphDatasetError(
                        f"{path.name}: skills[{index}].aliases[{alias_index}] "
                        "must be a non-empty string"
                    )
                _register_alias(
                    aliases,
                    alias_owner,
                    alias,
                    canonical_name,
                    path.name,
                )

        for index, role in enumerate(file_roles):
            location = f"roles[{index}]"
            _require_type(role, dict, path, location)
            name = _required_text(role, "name", path, location)
            role_key = normalize_skill_term(name)
            if role_key in role_by_key:
                raise SkillGraphDatasetError(
                    f"{path.name}: duplicate role {name!r}; "
                    f"already defined as {role_by_key[role_key]!r}"
                )
            aliases_value = role.get("aliases", [])
            _require_type(aliases_value, list, path, f"{location}.aliases")
            role_aliases = []
            for alias_index, alias in enumerate(aliases_value):
                if not isinstance(alias, str) or not alias.strip():
                    raise SkillGraphDatasetError(
                        f"{path.name}: {location}.aliases[{alias_index}] "
                        "must be a non-empty string"
                    )
                role_aliases.append(alias.strip())
            description = role.get("description", "")
            if not isinstance(description, str):
                raise SkillGraphDatasetError(
                    f"{path.name}: {location}.description must be a string"
                )
            role_by_key[role_key] = name
            roles.append(
                SkillGraphRole(
                    name=name,
                    aliases=tuple(role_aliases),
                    domain=domain,
                    description=description.strip(),
                )
            )

    for (
        path,
        domain,
        _,
        file_relationships,
        _,
        file_role_requirements,
    ) in payloads:
        for index, relationship in enumerate(file_relationships):
            location = f"relationships[{index}]"
            _require_type(relationship, dict, path, location)
            source = _required_text(relationship, "source", path, location)
            target = _required_text(relationship, "target", path, location)
            relationship_type = _required_text(
                relationship,
                "type",
                path,
                location,
            )
            if relationship_type not in ALLOWED_RELATIONSHIP_TYPES:
                raise SkillGraphDatasetError(
                    f"{path.name}: {location}.type must be one of "
                    f"{sorted(ALLOWED_RELATIONSHIP_TYPES)}"
                )
            confidence = relationship.get("confidence")
            if (
                not isinstance(confidence, (int, float))
                or isinstance(confidence, bool)
                or not 0 < float(confidence) <= 1
            ):
                raise SkillGraphDatasetError(
                    f"{path.name}: {location}.confidence must be above 0 and at most 1"
                )

            source_key = normalize_skill_term(source)
            target_key = normalize_skill_term(target)
            if source_key not in canonical_by_key:
                raise SkillGraphDatasetError(
                    f"{path.name}: {location}.source references unknown skill {source!r}"
                )
            if target_key not in canonical_by_key:
                raise SkillGraphDatasetError(
                    f"{path.name}: {location}.target references unknown skill {target!r}"
                )
            key = (source_key, target_key, relationship_type)
            if key in relationship_keys:
                raise SkillGraphDatasetError(
                    f"{path.name}: duplicate relationship "
                    f"{source!r} -> {target!r} ({relationship_type})"
                )
            relationship_keys.add(key)
            relationships.append(
                SkillGraphRelationship(
                    source=canonical_by_key[source_key],
                    target=canonical_by_key[target_key],
                    relationship_type=relationship_type,
                    confidence=float(confidence),
                    domain=domain,
                )
            )

        for index, requirement in enumerate(file_role_requirements):
            location = f"role_requirements[{index}]"
            _require_type(requirement, dict, path, location)
            role = _required_text(requirement, "role", path, location)
            skill = _required_text(requirement, "skill", path, location)
            importance = _required_text(
                requirement,
                "importance",
                path,
                location,
            )
            if importance not in {"required", "preferred"}:
                raise SkillGraphDatasetError(
                    f"{path.name}: {location}.importance must be "
                    "'required' or 'preferred'"
                )
            confidence = requirement.get("confidence")
            if (
                not isinstance(confidence, (int, float))
                or isinstance(confidence, bool)
                or not 0 < float(confidence) <= 1
            ):
                raise SkillGraphDatasetError(
                    f"{path.name}: {location}.confidence must be above 0 and at most 1"
                )
            role_key = normalize_skill_term(role)
            skill_key = normalize_skill_term(skill)
            if role_key not in role_by_key:
                raise SkillGraphDatasetError(
                    f"{path.name}: {location}.role references unknown role {role!r}"
                )
            if skill_key not in canonical_by_key:
                raise SkillGraphDatasetError(
                    f"{path.name}: {location}.skill references unknown skill {skill!r}"
                )
            key = (role_key, skill_key)
            if key in role_requirement_keys:
                raise SkillGraphDatasetError(
                    f"{path.name}: duplicate role requirement {role!r} -> {skill!r}"
                )
            role_requirement_keys.add(key)
            role_requirements.append(
                SkillGraphRoleRequirement(
                    role=role_by_key[role_key],
                    skill=canonical_by_key[skill_key],
                    importance=importance,
                    confidence=float(confidence),
                    domain=domain,
                )
            )

    return SkillGraphDataset(
        canonical_names=tuple(
            sorted(canonical_by_key.values(), key=str.casefold)
        ),
        aliases=aliases,
        relationships=tuple(relationships),
        roles=tuple(sorted(roles, key=lambda role: role.name.casefold())),
        role_requirements=tuple(role_requirements),
        source_files=tuple(path.name for path in files),
    )


def validate_skill_graph_dataset() -> dict:
    load_skill_graph_dataset.cache_clear()
    dataset = load_skill_graph_dataset()
    return {
        "files": len(dataset.source_files),
        "skills": len(dataset.canonical_names),
        "aliases": len(dataset.aliases),
        "relationships": len(dataset.relationships),
        "roles": len(dataset.roles),
        "role_requirements": len(dataset.role_requirements),
    }


def normalize_skill_term(skill_name: str) -> str:
    normalized = skill_name.casefold()
    normalized = normalized.replace(".", " ").replace("-", " ").replace("_", " ")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _register_alias(
    aliases: dict[str, str],
    owners: dict[str, str],
    alias: str,
    canonical_name: str,
    owner: str,
) -> None:
    alias_key = normalize_skill_term(alias)
    existing = aliases.get(alias_key)
    if existing and normalize_skill_term(existing) != normalize_skill_term(
        canonical_name
    ):
        raise SkillGraphDatasetError(
            f"{owner}: alias {alias!r} maps to {canonical_name!r}, but "
            f"{owners[alias_key]} maps it to {existing!r}"
        )
    aliases[alias_key] = canonical_name
    owners[alias_key] = owner


def _required_text(
    payload: dict,
    key: str,
    path: Path,
    location: str = "root",
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SkillGraphDatasetError(
            f"{path.name}: {location}.{key} must be a non-empty string"
        )
    return value.strip()


def _require_type(
    value: object,
    expected_type: type,
    path: Path,
    location: str,
) -> None:
    if not isinstance(value, expected_type):
        raise SkillGraphDatasetError(
            f"{path.name}: {location} must be a {expected_type.__name__}"
        )
