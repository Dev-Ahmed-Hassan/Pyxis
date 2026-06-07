import uuid

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from schemas.matching import (
    LlmRetrievedEvidence,
    SemanticSkillEvidence,
    SemanticSkillScore,
)
from services.ai.config import AIConfigurationError, get_embedding_route

SEMANTIC_EVIDENCE_THRESHOLD = 0.72
LLM_RETRIEVAL_TOP_K = 3


def get_semantic_skill_score(
    database: Session,
    resume_id: uuid.UUID,
    internship_id: uuid.UUID,
) -> SemanticSkillScore:
    try:
        route = get_embedding_route()
    except AIConfigurationError as error:
        return _unavailable_score(str(error))
    if not route:
        return _unavailable_score("Semantic embeddings are not configured.")

    try:
        storage_ready = database.scalar(
            text(
                "SELECT to_regclass("
                "'public.resume_section_embeddings'"
                ") IS NOT NULL "
                "AND to_regclass("
                "'public.internship_requirement_embeddings'"
                ") IS NOT NULL"
            )
        )
        if not storage_ready:
            return _unavailable_score(
                "Semantic embedding storage is unavailable. "
                "Apply the pgvector migration and refresh embeddings."
            )
        rows = database.execute(
            text(
                """
                SELECT
                    requirement.requirement,
                    requirement.requirement_category,
                    resume.section_type,
                    resume.section_key,
                    resume.section_text,
                    1 - (resume.embedding <=> requirement.embedding)
                        AS cosine_similarity
                FROM public.resume_section_embeddings AS resume
                JOIN public.internship_requirement_embeddings AS requirement
                  ON requirement.model_name = resume.model_name
                WHERE resume.resume_id = :resume_id
                  AND requirement.internship_input_id = :internship_id
                  AND resume.model_name = :model_name
                ORDER BY requirement.requirement_category,
                         requirement.requirement,
                         cosine_similarity DESC
                """
            ),
            {
                "resume_id": resume_id,
                "internship_id": internship_id,
                "model_name": route.model,
            },
        ).mappings()
    except SQLAlchemyError:
        return _unavailable_score(
            "Semantic embedding storage is unavailable. "
            "Apply the pgvector migration and refresh embeddings."
        )

    strongest_by_requirement = {}
    for row in rows:
        similarity = float(row["cosine_similarity"])
        if similarity < SEMANTIC_EVIDENCE_THRESHOLD:
            continue
        key = (row["requirement_category"], row["requirement"].casefold())
        strongest_by_requirement.setdefault(
            key,
            SemanticSkillEvidence(
                requirement=row["requirement"],
                requirement_category=row["requirement_category"],
                resume_section=row["section_type"],
                resume_section_key=row["section_key"],
                resume_text_excerpt=_excerpt(row["section_text"]),
                cosine_similarity=round(similarity, 4),
                threshold=SEMANTIC_EVIDENCE_THRESHOLD,
                source="pgvector",
            ),
        )

    evidence = list(strongest_by_requirement.values())
    warning = None
    if not evidence:
        warning = (
            "No semantic evidence met the reporting threshold. This does not prove "
            "the resume is unrelated to the internship."
        )
    return SemanticSkillScore(
        available=True,
        contributes_to_score=False,
        model_name=route.model,
        reporting_threshold=SEMANTIC_EVIDENCE_THRESHOLD,
        evidence=evidence,
        warnings=[warning] if warning else [],
    )


def get_llm_retrieval_candidates(
    database: Session,
    resume_id: uuid.UUID,
    internship_id: uuid.UUID,
    missing_requirements: set[tuple[str, str]],
    top_k: int = LLM_RETRIEVAL_TOP_K,
) -> list[LlmRetrievedEvidence]:
    try:
        route = get_embedding_route()
    except AIConfigurationError:
        return []
    if not route:
        return []

    try:
        rows = database.execute(
            text(
                """
                SELECT
                    requirement.requirement,
                    requirement.requirement_category,
                    resume.section_type,
                    resume.section_key,
                    resume.section_text,
                    1 - (resume.embedding <=> requirement.embedding)
                        AS cosine_similarity
                FROM public.resume_section_embeddings AS resume
                JOIN public.internship_requirement_embeddings AS requirement
                  ON requirement.model_name = resume.model_name
                WHERE resume.resume_id = :resume_id
                  AND requirement.internship_input_id = :internship_id
                  AND resume.model_name = :model_name
                ORDER BY requirement.requirement_category,
                         requirement.requirement,
                         cosine_similarity DESC
                """
            ),
            {
                "resume_id": resume_id,
                "internship_id": internship_id,
                "model_name": route.model,
            },
        ).mappings()
    except SQLAlchemyError:
        return []

    candidate_counts: dict[tuple[str, str], int] = {}
    candidates = []
    for row in rows:
        key = (
            row["requirement_category"],
            row["requirement"].casefold(),
        )
        if key not in missing_requirements:
            continue
        if candidate_counts.get(key, 0) >= top_k:
            continue
        candidates.append(
            LlmRetrievedEvidence(
                requirement=row["requirement"],
                requirement_category=row["requirement_category"],
                resume_section=row["section_type"],
                resume_section_key=row["section_key"],
                resume_text_excerpt=_excerpt(row["section_text"]),
                cosine_similarity=round(float(row["cosine_similarity"]), 4),
                source="pgvector",
            )
        )
        candidate_counts[key] = candidate_counts.get(key, 0) + 1
    return candidates


def _unavailable_score(reason: str) -> SemanticSkillScore:
    return SemanticSkillScore(
        available=False,
        contributes_to_score=False,
        model_name=None,
        reporting_threshold=SEMANTIC_EVIDENCE_THRESHOLD,
        evidence=[],
        warnings=[reason],
    )


def _excerpt(value: str, limit: int = 240) -> str:
    return value if len(value) <= limit else value[: limit - 3].rstrip() + "..."
