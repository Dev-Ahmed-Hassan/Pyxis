from dataclasses import dataclass

from services.ai.internship_schemas import ParsedInternship
from services.ai.schemas import ExtractedSkill, ParsedResume
from services.skill_graph_dataset_service import (
    load_skill_graph_dataset,
    normalize_skill_term,
)

SKILL_ALIASES = load_skill_graph_dataset().aliases


@dataclass(frozen=True)
class CanonicalSkill:
    original_name: str
    canonical_name: str


class SkillCanonicalizer:
    def canonicalize(self, skill_name: str) -> CanonicalSkill:
        original_name = skill_name.strip()
        lookup_key = normalize_skill_term(original_name)
        return CanonicalSkill(
            original_name=original_name,
            canonical_name=SKILL_ALIASES.get(lookup_key, original_name),
        )


def canonicalize_parsed_resume(
    parsed_resume: ParsedResume,
    canonicalizer: SkillCanonicalizer | None = None,
) -> ParsedResume:
    canonicalizer = canonicalizer or SkillCanonicalizer()
    parsed_resume.skills = [
        _canonicalize_extracted_skill(skill, canonicalizer) for skill in parsed_resume.skills
    ]
    for experience in parsed_resume.experience:
        experience.skills = [
            _canonicalize_extracted_skill(skill, canonicalizer) for skill in experience.skills
        ]
    for project in parsed_resume.projects:
        project.skills = [
            _canonicalize_extracted_skill(skill, canonicalizer) for skill in project.skills
        ]
    return parsed_resume


def canonicalize_parsed_internship(
    parsed_internship: ParsedInternship,
    canonicalizer: SkillCanonicalizer | None = None,
) -> ParsedInternship:
    canonicalizer = canonicalizer or SkillCanonicalizer()
    parsed_internship.required_skills = [
        _canonicalize_extracted_skill(skill, canonicalizer)
        for skill in parsed_internship.required_skills
    ]
    parsed_internship.preferred_skills = [
        _canonicalize_extracted_skill(skill, canonicalizer)
        for skill in parsed_internship.preferred_skills
    ]
    parsed_internship.required_domain_concepts = [
        _canonicalize_extracted_skill(skill, canonicalizer)
        for skill in parsed_internship.required_domain_concepts
    ]
    parsed_internship.preferred_domain_concepts = [
        _canonicalize_extracted_skill(skill, canonicalizer)
        for skill in parsed_internship.preferred_domain_concepts
    ]
    parsed_internship.required_soft_skills = [
        _canonicalize_extracted_skill(skill, canonicalizer)
        for skill in parsed_internship.required_soft_skills
    ]
    parsed_internship.preferred_soft_skills = [
        _canonicalize_extracted_skill(skill, canonicalizer)
        for skill in parsed_internship.preferred_soft_skills
    ]
    return parsed_internship


def _canonicalize_extracted_skill(
    skill: ExtractedSkill,
    canonicalizer: SkillCanonicalizer,
) -> ExtractedSkill:
    canonical_skill = canonicalizer.canonicalize(skill.name)
    return skill.model_copy(
        update={
            "name": canonical_skill.original_name,
            "canonical_name": canonical_skill.canonical_name,
        }
    )
