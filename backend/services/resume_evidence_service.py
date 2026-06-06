from services.ai.schemas import ExtractedSkill, ParsedResume
from services.skill_canonicalizer import SkillCanonicalizer
from schemas.matching import ResumeEvidenceSection, ResumeSkillEvidence

SECTION_PROVENANCE_WEIGHTS = {
    "skills_list": 0.75,
    "project": 0.9,
    "experience": 1.0,
    "certification": 0.85,
}
EXTRACTION_SOURCE_WEIGHTS = {
    "explicit": 1.0,
    "inferred": 0.65,
    "manual": 1.0,
}


def collect_resume_skill_evidence(parsed_resume: ParsedResume) -> list[ResumeSkillEvidence]:
    evidence = []
    evidence.extend(
        _skill_evidence(skill, section="skills_list")
        for skill in parsed_resume.skills
    )
    for project in parsed_resume.projects:
        evidence.extend(
            _skill_evidence(skill, section="project", context=project.name)
            for skill in project.skills
        )
    for experience in parsed_resume.experience:
        context = " at ".join(
            value for value in (experience.role, experience.company) if value
        )
        evidence.extend(
            _skill_evidence(
                skill,
                section="experience",
                context=context or None,
            )
            for skill in experience.skills
        )
    canonicalizer = SkillCanonicalizer()
    evidence.extend(
        ResumeSkillEvidence(
            skill=canonicalizer.canonicalize(certification.name).canonical_name,
            section="certification",
            extraction_source="explicit",
            confidence=certification.confidence,
            provenance_weight=SECTION_PROVENANCE_WEIGHTS["certification"],
            context=certification.issuer,
        )
        for certification in parsed_resume.certifications
    )
    return evidence


def strongest_resume_evidence_by_skill(
    evidence: list[ResumeSkillEvidence],
) -> dict[str, ResumeSkillEvidence]:
    strongest = {}
    for item in evidence:
        key = item.skill.casefold()
        existing = strongest.get(key)
        if existing is None or _evidence_strength(item) > _evidence_strength(existing):
            strongest[key] = item
    return strongest


def unique_resume_skill_names(evidence: list[ResumeSkillEvidence]) -> list[str]:
    unique_names = {}
    for item in evidence:
        unique_names.setdefault(item.skill.casefold(), item.skill)
    return list(unique_names.values())


def _skill_evidence(
    skill: ExtractedSkill,
    section: ResumeEvidenceSection,
    context: str | None = None,
) -> ResumeSkillEvidence:
    canonical_name = (skill.canonical_name or skill.name).strip()
    provenance_weight = (
        SECTION_PROVENANCE_WEIGHTS[section] * EXTRACTION_SOURCE_WEIGHTS[skill.source]
    )
    return ResumeSkillEvidence(
        skill=canonical_name,
        section=section,
        extraction_source=skill.source,
        confidence=skill.confidence,
        provenance_weight=round(provenance_weight, 4),
        context=context,
    )


def _evidence_strength(evidence: ResumeSkillEvidence) -> tuple[float, float]:
    return evidence.provenance_weight, evidence.confidence
