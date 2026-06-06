import hashlib
import uuid

from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.ai.config import AIConfigurationError, get_embedding_route


class SemanticCalibrationCandidate(BaseModel):
    id: str
    domain: str
    resume_section: str
    resume_text: str
    requirement: str
    cosine_similarity: float
    should_report: None = None
    source: str = "pending_review"
    reviewer_note: str = ""


def collect_semantic_calibration_candidates(
    database: Session,
    resume_id: uuid.UUID,
    internship_id: uuid.UUID,
) -> list[SemanticCalibrationCandidate]:
    route = get_embedding_route()
    if not route:
        raise AIConfigurationError("Semantic embeddings are not configured")
    rows = database.execute(
        text(
            """
            SELECT
                requirement.requirement,
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
            ORDER BY requirement.requirement, cosine_similarity DESC
            """
        ),
        {
            "resume_id": resume_id,
            "internship_id": internship_id,
            "model_name": route.model,
        },
    ).mappings()
    return [
        SemanticCalibrationCandidate(
            id=_candidate_id(
                resume_id,
                internship_id,
                row["section_type"],
                row["section_key"],
                row["requirement"],
            ),
            domain="review_me",
            resume_section=row["section_type"],
            resume_text=row["section_text"],
            requirement=row["requirement"],
            cosine_similarity=round(float(row["cosine_similarity"]), 4),
        )
        for row in rows
    ]


def _candidate_id(
    resume_id: uuid.UUID,
    internship_id: uuid.UUID,
    section_type: str,
    section_key: str,
    requirement: str,
) -> str:
    value = ":".join(
        [
            str(resume_id),
            str(internship_id),
            section_type,
            section_key,
            requirement.casefold(),
        ]
    )
    return "live-" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
