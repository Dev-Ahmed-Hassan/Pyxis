from collections import defaultdict
from decimal import Decimal

from fastapi import HTTPException, status
from pymongo.errors import PyMongoError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from database.mongodb import get_mongodb_database
from models.resume import Resume, ResumeProcessingStatus
from models.user import User
from models.user_profile_facts import (
    UserProfileCertificationSource,
    UserProfileProjectSource,
    UserProfileSkillSource,
)
from schemas.profile import (
    UserProfileCertificationSourceResponse,
    UserProfileFactsRefreshResponse,
    UserProfileFactsResponse,
    UserProfileProjectSourceResponse,
    UserProfileSkillInventoryItem,
    UserProfileSkillSourceResponse,
)
from services.ai.schemas import ParsedResume


def refresh_user_profile_facts(
    database: Session,
    user: User,
) -> UserProfileFactsRefreshResponse:
    resumes = _ready_active_resumes(database, user)
    _delete_user_profile_facts(database, user.id)
    parsed_by_resume = _load_parsed_resumes(resumes)

    skill_count = 0
    project_count = 0
    certification_count = 0
    for resume in resumes:
        parsed_resume = parsed_by_resume.get(str(resume.id))
        if not parsed_resume:
            continue
        skill_count += _add_skill_sources(database, user.id, resume.id, parsed_resume)
        project_count += _add_project_sources(database, user.id, resume.id, parsed_resume)
        certification_count += _add_certification_sources(
            database,
            user.id,
            resume.id,
            parsed_resume,
        )

    database.commit()
    response = get_user_profile_facts(database, user)
    return UserProfileFactsRefreshResponse(
        **response.model_dump(),
        refreshed_resume_count=len(parsed_by_resume),
        skill_source_count=skill_count,
        project_source_count=project_count,
        certification_source_count=certification_count,
    )


def replace_profile_facts_for_resume(
    database: Session,
    user_id,
    resume_id,
    parsed_resume: ParsedResume,
) -> None:
    delete_profile_facts_for_resume(database, resume_id)
    _add_skill_sources(database, user_id, resume_id, parsed_resume)
    _add_project_sources(database, user_id, resume_id, parsed_resume)
    _add_certification_sources(database, user_id, resume_id, parsed_resume)


def get_user_profile_facts(
    database: Session,
    user: User,
) -> UserProfileFactsResponse:
    skill_sources = list(
        database.scalars(
            select(UserProfileSkillSource)
            .where(UserProfileSkillSource.user_id == user.id)
            .order_by(UserProfileSkillSource.canonical_name, UserProfileSkillSource.created_at)
        )
    )
    project_sources = list(
        database.scalars(
            select(UserProfileProjectSource)
            .where(UserProfileProjectSource.user_id == user.id)
            .order_by(UserProfileProjectSource.created_at)
        )
    )
    certification_sources = list(
        database.scalars(
            select(UserProfileCertificationSource)
            .where(UserProfileCertificationSource.user_id == user.id)
            .order_by(UserProfileCertificationSource.created_at)
        )
    )
    return UserProfileFactsResponse(
        user_id=user.id,
        skill_inventory=_build_skill_inventory(skill_sources),
        skill_sources=[_skill_source_response(source) for source in skill_sources],
        project_sources=[_project_source_response(source) for source in project_sources],
        certification_sources=[
            _certification_source_response(source) for source in certification_sources
        ],
    )


def delete_profile_facts_for_resume(database: Session, resume_id) -> None:
    database.execute(
        delete(UserProfileSkillSource).where(UserProfileSkillSource.resume_id == resume_id)
    )
    database.execute(
        delete(UserProfileProjectSource).where(UserProfileProjectSource.resume_id == resume_id)
    )
    database.execute(
        delete(UserProfileCertificationSource).where(
            UserProfileCertificationSource.resume_id == resume_id
        )
    )


def _ready_active_resumes(database: Session, user: User) -> list[Resume]:
    return list(
        database.scalars(
            select(Resume)
            .where(
                Resume.user_id == user.id,
                Resume.deleted_at.is_(None),
                Resume.processing_status == ResumeProcessingStatus.READY,
            )
            .order_by(Resume.created_at.desc())
        )
    )


def _load_parsed_resumes(resumes: list[Resume]) -> dict[str, ParsedResume]:
    if not resumes:
        return {}
    resume_ids = [str(resume.id) for resume in resumes]
    try:
        documents = list(
            get_mongodb_database().resumes.find(
                {"postgres_resume_id": {"$in": resume_ids}},
                {"postgres_resume_id": 1, "parsed_resume": 1},
            )
        )
    except PyMongoError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Parsed resume storage is temporarily unavailable",
        ) from error

    parsed_by_resume = {}
    for document in documents:
        try:
            parsed_by_resume[document["postgres_resume_id"]] = ParsedResume.model_validate(
                document["parsed_resume"]
            )
        except (KeyError, ValueError):
            continue
    return parsed_by_resume


def _add_skill_sources(database, user_id, resume_id, parsed_resume: ParsedResume) -> int:
    count = 0
    for index, skill in enumerate(parsed_resume.skills):
        database.add(
            _skill_source(
                user_id,
                resume_id,
                skill,
                source_section="skills_list",
                source_key=f"skills_list:{index}",
                context=None,
            )
        )
        count += 1

    for project_index, project in enumerate(parsed_resume.projects):
        context = project.name
        for skill_index, skill in enumerate(project.skills):
            database.add(
                _skill_source(
                    user_id,
                    resume_id,
                    skill,
                    source_section="project",
                    source_key=f"project:{project_index}:skill:{skill_index}",
                    context=context,
                )
            )
            count += 1

    for experience_index, experience in enumerate(parsed_resume.experience):
        context = " - ".join(
            value for value in [experience.role, experience.company] if value
        )
        for skill_index, skill in enumerate(experience.skills):
            database.add(
                _skill_source(
                    user_id,
                    resume_id,
                    skill,
                    source_section="experience",
                    source_key=f"experience:{experience_index}:skill:{skill_index}",
                    context=context or None,
                )
            )
            count += 1
    return count


def _skill_source(
    user_id,
    resume_id,
    skill,
    source_section: str,
    source_key: str,
    context: str | None,
) -> UserProfileSkillSource:
    canonical_name = (skill.canonical_name or skill.name).strip()
    return UserProfileSkillSource(
        user_id=user_id,
        resume_id=resume_id,
        skill_name=skill.name.strip(),
        canonical_name=canonical_name,
        source_section=source_section,
        source_key=source_key,
        extraction_source=skill.source,
        confidence=Decimal(str(round(float(skill.confidence), 3))),
        evidence=skill.evidence,
        context=context,
    )


def _add_project_sources(database, user_id, resume_id, parsed_resume: ParsedResume) -> int:
    for index, project in enumerate(parsed_resume.projects):
        database.add(
            UserProfileProjectSource(
                user_id=user_id,
                resume_id=resume_id,
                source_key=f"project:{index}",
                project_name=project.name,
                description=project.description,
                skills=[skill.canonical_name or skill.name for skill in project.skills],
                confidence=Decimal(str(round(float(project.confidence), 3))),
                evidence=project.evidence,
            )
        )
    return len(parsed_resume.projects)


def _add_certification_sources(database, user_id, resume_id, parsed_resume: ParsedResume) -> int:
    for index, certification in enumerate(parsed_resume.certifications):
        database.add(
            UserProfileCertificationSource(
                user_id=user_id,
                resume_id=resume_id,
                source_key=f"certification:{index}",
                certification_name=certification.name,
                issuer=certification.issuer,
                date=certification.date,
                confidence=Decimal(str(round(float(certification.confidence), 3))),
                evidence=certification.evidence,
            )
        )
    return len(parsed_resume.certifications)


def _delete_user_profile_facts(database: Session, user_id) -> None:
    database.execute(delete(UserProfileSkillSource).where(UserProfileSkillSource.user_id == user_id))
    database.execute(delete(UserProfileProjectSource).where(UserProfileProjectSource.user_id == user_id))
    database.execute(
        delete(UserProfileCertificationSource).where(
            UserProfileCertificationSource.user_id == user_id
        )
    )


def _build_skill_inventory(
    sources: list[UserProfileSkillSource],
) -> list[UserProfileSkillInventoryItem]:
    grouped = defaultdict(list)
    for source in sources:
        grouped[source.canonical_name.casefold()].append(source)

    inventory = []
    for grouped_sources in grouped.values():
        best = max(grouped_sources, key=lambda source: float(source.confidence))
        source_sections = sorted({source.source_section for source in grouped_sources})
        inventory.append(
            UserProfileSkillInventoryItem(
                canonical_name=best.canonical_name,
                display_name=best.canonical_name,
                strength=_skill_strength(grouped_sources),
                source_count=len(grouped_sources),
                resume_ids=sorted({source.resume_id for source in grouped_sources}, key=str),
                source_sections=source_sections,
                best_confidence=float(best.confidence),
                best_evidence=best.evidence,
            )
        )
    return sorted(
        inventory,
        key=lambda item: (-item.source_count, -item.best_confidence, item.display_name.casefold()),
    )


def _skill_strength(sources: list[UserProfileSkillSource]) -> str:
    sections = {source.source_section for source in sources}
    best_confidence = max(float(source.confidence) for source in sources)
    if {"project", "experience"} & sections or len(sources) >= 3 or best_confidence >= 0.9:
        return "strong"
    if len(sources) >= 2 or best_confidence >= 0.75:
        return "moderate"
    return "emerging"


def _skill_source_response(source: UserProfileSkillSource) -> UserProfileSkillSourceResponse:
    return UserProfileSkillSourceResponse(
        id=source.id,
        resume_id=source.resume_id,
        skill_name=source.skill_name,
        canonical_name=source.canonical_name,
        source_section=source.source_section,
        source_key=source.source_key,
        extraction_source=source.extraction_source,
        confidence=float(source.confidence),
        evidence=source.evidence,
        context=source.context,
        created_at=source.created_at,
    )


def _project_source_response(source: UserProfileProjectSource) -> UserProfileProjectSourceResponse:
    return UserProfileProjectSourceResponse(
        id=source.id,
        resume_id=source.resume_id,
        source_key=source.source_key,
        project_name=source.project_name,
        description=source.description,
        skills=source.skills,
        confidence=float(source.confidence),
        evidence=source.evidence,
        created_at=source.created_at,
    )


def _certification_source_response(
    source: UserProfileCertificationSource,
) -> UserProfileCertificationSourceResponse:
    return UserProfileCertificationSourceResponse(
        id=source.id,
        resume_id=source.resume_id,
        source_key=source.source_key,
        certification_name=source.certification_name,
        issuer=source.issuer,
        date=source.date,
        confidence=float(source.confidence),
        evidence=source.evidence,
        created_at=source.created_at,
    )
