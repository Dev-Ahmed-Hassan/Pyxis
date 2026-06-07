import hashlib
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from services.ai.config import (
    AIConfigurationError,
    get_embedding_dimensions,
    get_embedding_route,
    get_provider_keys,
)
from services.ai.internship_schemas import ParsedInternship
from services.ai.providers.gemini_embeddings import (
    GeminiEmbeddingProvider,
    TextEmbedding,
)
from services.ai.providers.base import AIProviderError
from services.ai.schemas import ParsedResume


@dataclass(frozen=True)
class ResumeSectionDocument:
    section_type: str
    section_key: str
    text: str


@dataclass(frozen=True)
class InternshipRequirementDocument:
    requirement_category: str
    requirement: str
    text: str


class EmbeddingProvider(Protocol):
    def embed(self, text: str) -> TextEmbedding:
        ...


@dataclass(frozen=True)
class BestEffortEmbeddingRefresh:
    refreshed: bool
    document_count: int
    warning: str | None = None


def build_embedding_provider() -> EmbeddingProvider | None:
    route = get_embedding_route()
    if not route:
        return None
    if route.provider != "gemini":
        raise AIConfigurationError(
            f"Unsupported embedding provider '{route.provider}'"
        )
    return GeminiEmbeddingProvider(
        route=route,
        api_keys=get_provider_keys(route.provider),
        dimensions=get_embedding_dimensions(),
    )


def build_resume_section_documents(
    parsed_resume: ParsedResume,
) -> list[ResumeSectionDocument]:
    documents = []
    if parsed_resume.skills:
        documents.append(
            ResumeSectionDocument(
                section_type="skills_list",
                section_key="skills_list",
                text=_join_text(
                    [
                        "Listed skills",
                        ", ".join(
                            skill.canonical_name or skill.name
                            for skill in parsed_resume.skills
                        ),
                    ]
                ),
            )
        )
    if parsed_resume.summary.value:
        documents.append(
            ResumeSectionDocument(
                section_type="summary",
                section_key="summary",
                text=parsed_resume.summary.value.strip(),
            )
        )
    for index, project in enumerate(parsed_resume.projects):
        documents.append(
            ResumeSectionDocument(
                section_type="project",
                section_key=f"project:{index}",
                text=_join_text([project.name, *project.description]),
            )
        )
        documents.extend(
            ResumeSectionDocument(
                section_type="project",
                section_key=f"project:{index}:bullet:{bullet_index}",
                text=_join_text([project.name, bullet]),
            )
            for bullet_index, bullet in enumerate(project.description)
        )
    for index, experience in enumerate(parsed_resume.experience):
        documents.append(
            ResumeSectionDocument(
                section_type="experience",
                section_key=f"experience:{index}",
                text=_join_text(
                    [experience.role, experience.company, *experience.description]
                ),
            )
        )
        documents.extend(
            ResumeSectionDocument(
                section_type="experience",
                section_key=f"experience:{index}:bullet:{bullet_index}",
                text=_join_text([experience.role, experience.company, bullet]),
            )
            for bullet_index, bullet in enumerate(experience.description)
        )
    documents.extend(
        ResumeSectionDocument(
            section_type="education",
            section_key=f"education:{index}",
            text=_join_text(
                [education.degree, education.field_of_study, education.institution]
            ),
        )
        for index, education in enumerate(parsed_resume.education)
    )
    documents.extend(
        ResumeSectionDocument(
            section_type="certification",
            section_key=f"certification:{index}",
            text=_join_text([certification.name, certification.issuer]),
        )
        for index, certification in enumerate(parsed_resume.certifications)
    )
    return [document for document in documents if document.text]


def build_internship_requirement_documents(
    parsed_internship: ParsedInternship,
) -> list[InternshipRequirementDocument]:
    documents = []
    for field, category in (
        ("required_skills", "required_skill"),
        ("preferred_skills", "preferred_skill"),
    ):
        seen = set()
        for skill in getattr(parsed_internship, field):
            requirement = (skill.canonical_name or skill.name).strip()
            key = requirement.casefold()
            if requirement and key not in seen:
                documents.append(
                    InternshipRequirementDocument(
                        requirement_category=category,
                        requirement=requirement,
                        text=_build_requirement_text(requirement, parsed_internship),
                    )
                )
                seen.add(key)
    return documents


def refresh_resume_section_embeddings(
    database: Session,
    resume_id,
    parsed_resume: ParsedResume,
    provider: EmbeddingProvider | None = None,
) -> int:
    provider = provider or build_embedding_provider()
    if not provider:
        return 0
    documents = build_resume_section_documents(parsed_resume)
    database.execute(
        text("DELETE FROM public.resume_section_embeddings WHERE resume_id = :resume_id"),
        {"resume_id": resume_id},
    )
    for document in documents:
        embedding = provider.embed(document.text)
        database.execute(
            text(
                """
                INSERT INTO public.resume_section_embeddings (
                    resume_id, section_type, section_key, section_text,
                    content_hash, model_name, embedding
                ) VALUES (
                    :resume_id, :section_type, :section_key, :section_text,
                    :content_hash, :model_name,
                    CAST(:embedding AS extensions.vector(768))
                )
                """
            ),
            {
                "resume_id": resume_id,
                "section_type": document.section_type,
                "section_key": document.section_key,
                "section_text": document.text,
                "content_hash": _content_hash(document.text),
                "model_name": embedding.model_name,
                "embedding": _vector_literal(embedding.values),
            },
        )
    return len(documents)


def refresh_internship_requirement_embeddings(
    database: Session,
    internship_id,
    parsed_internship: ParsedInternship,
    provider: EmbeddingProvider | None = None,
) -> int:
    provider = provider or build_embedding_provider()
    if not provider:
        return 0
    documents = build_internship_requirement_documents(parsed_internship)
    database.execute(
        text(
            "DELETE FROM public.internship_requirement_embeddings "
            "WHERE internship_input_id = :internship_id"
        ),
        {"internship_id": internship_id},
    )
    for document in documents:
        embedding = provider.embed(document.text)
        database.execute(
            text(
                """
                INSERT INTO public.internship_requirement_embeddings (
                    internship_input_id, requirement_category, requirement,
                    requirement_text, content_hash, model_name, embedding
                ) VALUES (
                    :internship_id, :requirement_category, :requirement,
                    :requirement_text, :content_hash, :model_name,
                    CAST(:embedding AS extensions.vector(768))
                )
                """
            ),
            {
                "internship_id": internship_id,
                "requirement_category": document.requirement_category,
                "requirement": document.requirement,
                "requirement_text": document.text,
                "content_hash": _content_hash(document.text),
                "model_name": embedding.model_name,
                "embedding": _vector_literal(embedding.values),
            },
        )
    return len(documents)


def invalidate_resume_section_embeddings(database: Session, resume_id) -> bool:
    return _best_effort_delete(
        database,
        "DELETE FROM public.resume_section_embeddings WHERE resume_id = :resume_id",
        {"resume_id": resume_id},
    )


def invalidate_internship_requirement_embeddings(
    database: Session,
    internship_id,
) -> bool:
    return _best_effort_delete(
        database,
        "DELETE FROM public.internship_requirement_embeddings "
        "WHERE internship_input_id = :internship_id",
        {"internship_id": internship_id},
    )


def best_effort_refresh_resume_section_embeddings(
    database: Session,
    resume_id,
    parsed_resume: ParsedResume,
) -> BestEffortEmbeddingRefresh:
    return _best_effort_refresh(
        database,
        lambda: refresh_resume_section_embeddings(database, resume_id, parsed_resume),
    )


def best_effort_refresh_internship_requirement_embeddings(
    database: Session,
    internship_id,
    parsed_internship: ParsedInternship,
) -> BestEffortEmbeddingRefresh:
    return _best_effort_refresh(
        database,
        lambda: refresh_internship_requirement_embeddings(
            database,
            internship_id,
            parsed_internship,
        ),
    )


def _join_text(values: list[str | None]) -> str:
    return ". ".join(value.strip() for value in values if value and value.strip())


def _build_requirement_text(
    requirement: str,
    parsed_internship: ParsedInternship,
) -> str:
    tokens = {
        token
        for token in requirement.casefold().replace("/", " ").split()
        if len(token) > 2
    }
    context = [
        statement
        for statement in [
            *parsed_internship.responsibilities,
            *parsed_internship.qualifications,
        ]
        if any(token in statement.casefold() for token in tokens)
    ]
    return _join_text([requirement, parsed_internship.title.value, *context])


def _content_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(value) for value in values) + "]"


def _best_effort_delete(database: Session, statement: str, parameters: dict) -> bool:
    try:
        database.execute(text(statement), parameters)
        database.commit()
        return True
    except SQLAlchemyError:
        database.rollback()
        return False


def _best_effort_refresh(
    database: Session,
    refresh,
) -> BestEffortEmbeddingRefresh:
    try:
        document_count = refresh()
        database.commit()
        if document_count == 0 and not get_embedding_route():
            return BestEffortEmbeddingRefresh(
                refreshed=False,
                document_count=0,
                warning="Semantic embeddings are not configured.",
            )
        return BestEffortEmbeddingRefresh(
            refreshed=True,
            document_count=document_count,
        )
    except (AIConfigurationError, AIProviderError, SQLAlchemyError) as error:
        database.rollback()
        return BestEffortEmbeddingRefresh(
            refreshed=False,
            document_count=0,
            warning=str(error),
        )
