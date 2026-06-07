import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from schemas.matching import (
    MatchExplainabilityKnowledgeChunkResponse,
    MatchExplainabilityKnowledgeSearchResponse,
)
from services.ai.config import AIConfigurationError, get_embedding_route
from services.ai.providers.base import AIProviderError
from services.semantic_embedding_service import EmbeddingProvider, build_embedding_provider

KNOWLEDGE_NAMESPACE = "match_explainability"
KNOWLEDGE_ROOT = Path(__file__).resolve().parent.parent / "knowledge" / KNOWLEDGE_NAMESPACE
MIN_CHUNK_LENGTH = 80


@dataclass(frozen=True)
class KnowledgeChunk:
    source_path: str
    heading: str
    heading_path: str
    topic_tags: list[str]
    text: str


@dataclass(frozen=True)
class KnowledgeIndexResult:
    indexed: bool
    model_name: str | None
    source_file_count: int
    chunk_count: int
    warning: str | None = None


def refresh_match_explainability_knowledge_embeddings(
    database: Session,
    provider: EmbeddingProvider | None = None,
) -> KnowledgeIndexResult:
    provider = provider or build_embedding_provider()
    if not provider:
        return KnowledgeIndexResult(
            indexed=False,
            model_name=None,
            source_file_count=0,
            chunk_count=0,
            warning="Semantic embeddings are not configured.",
        )

    try:
        chunks = build_match_explainability_chunks()
        database.execute(
            text(
                """
                DELETE FROM public.match_explainability_knowledge_chunks
                WHERE namespace = :namespace
                """
            ),
            {"namespace": KNOWLEDGE_NAMESPACE},
        )

        model_name = None
        for chunk in chunks:
            embedding = provider.embed(chunk.text)
            model_name = embedding.model_name
            database.execute(
                text(
                    """
                    INSERT INTO public.match_explainability_knowledge_chunks (
                        namespace, source_path, heading, heading_path, topic_tags,
                        chunk_text, content_hash, model_name, embedding
                    ) VALUES (
                        :namespace, :source_path, :heading, :heading_path, :topic_tags,
                        :chunk_text, :content_hash, :model_name,
                        CAST(:embedding AS extensions.vector(768))
                    )
                    """
                ),
                {
                    "namespace": KNOWLEDGE_NAMESPACE,
                    "source_path": chunk.source_path,
                    "heading": chunk.heading,
                    "heading_path": chunk.heading_path,
                    "topic_tags": chunk.topic_tags,
                    "chunk_text": chunk.text,
                    "content_hash": _content_hash(chunk.text),
                    "model_name": embedding.model_name,
                    "embedding": _vector_literal(embedding.values),
                },
            )
        database.commit()
        return KnowledgeIndexResult(
            indexed=True,
            model_name=model_name,
            source_file_count=len(_knowledge_files()),
            chunk_count=len(chunks),
        )
    except (AIConfigurationError, AIProviderError, SQLAlchemyError) as error:
        database.rollback()
        return KnowledgeIndexResult(
            indexed=False,
            model_name=get_embedding_route().model if get_embedding_route() else None,
            source_file_count=len(_knowledge_files()),
            chunk_count=0,
            warning=str(error),
        )


def build_match_explainability_chunks() -> list[KnowledgeChunk]:
    chunks = []
    for path in _knowledge_files():
        chunks.extend(_chunks_from_markdown(path))
    return chunks


def search_match_explainability_knowledge(
    database: Session,
    query: str,
    limit: int = 6,
    provider: EmbeddingProvider | None = None,
) -> MatchExplainabilityKnowledgeSearchResponse:
    try:
        route = get_embedding_route()
    except AIConfigurationError as error:
        return _search_unavailable(query, str(error))
    if not route:
        return _search_unavailable(query, "Semantic embeddings are not configured.")

    provider = provider or build_embedding_provider()
    if not provider:
        return _search_unavailable(query, "Semantic embeddings are not configured.")

    try:
        storage_ready = database.scalar(
            text(
                "SELECT to_regclass("
                "'public.match_explainability_knowledge_chunks'"
                ") IS NOT NULL"
            )
        )
        if not storage_ready:
            return _search_unavailable(
                query,
                "Match explainability knowledge storage is unavailable. "
                "Apply migration 010 and refresh knowledge embeddings.",
            )

        embedding = provider.embed(query)
        rows = database.execute(
            text(
                """
                SELECT
                    id,
                    source_path,
                    heading,
                    heading_path,
                    topic_tags,
                    chunk_text,
                    1 - (embedding <=> CAST(:embedding AS extensions.vector(768)))
                        AS cosine_similarity
                FROM public.match_explainability_knowledge_chunks
                WHERE namespace = :namespace
                  AND model_name = :model_name
                ORDER BY embedding <=> CAST(:embedding AS extensions.vector(768))
                LIMIT :limit
                """
            ),
            {
                "namespace": KNOWLEDGE_NAMESPACE,
                "model_name": embedding.model_name,
                "embedding": _vector_literal(embedding.values),
                "limit": limit,
            },
        ).mappings()
    except (AIConfigurationError, AIProviderError, SQLAlchemyError) as error:
        return _search_unavailable(query, str(error), model_name=route.model)

    chunks = [
        MatchExplainabilityKnowledgeChunkResponse(
            id=row["id"],
            source_path=row["source_path"],
            heading=row["heading"],
            heading_path=row["heading_path"],
            topic_tags=list(row["topic_tags"] or []),
            chunk_text=_excerpt(row["chunk_text"]),
            cosine_similarity=round(float(row["cosine_similarity"]), 4),
        )
        for row in rows
    ]
    warning = None
    if not chunks:
        warning = (
            "No match explainability knowledge chunks were found. "
            "Refresh knowledge embeddings before building explanations."
        )
    return MatchExplainabilityKnowledgeSearchResponse(
        query=query,
        model_name=route.model,
        chunks=chunks,
        warning=warning,
    )


def _knowledge_files() -> list[Path]:
    if not KNOWLEDGE_ROOT.exists():
        return []
    return sorted(KNOWLEDGE_ROOT.glob("*.md"))


def _search_unavailable(
    query: str,
    warning: str,
    model_name: str | None = None,
) -> MatchExplainabilityKnowledgeSearchResponse:
    return MatchExplainabilityKnowledgeSearchResponse(
        query=query,
        model_name=model_name,
        chunks=[],
        warning=warning,
    )


def _chunks_from_markdown(path: Path) -> list[KnowledgeChunk]:
    text_content = path.read_text(encoding="utf-8").strip()
    if not text_content:
        return []

    lines = text_content.splitlines()
    title = _clean_heading(lines[0]) if lines and lines[0].startswith("# ") else path.stem
    sections = []
    current_heading = title
    current_lines = []

    for line in lines[1:]:
        if line.startswith("## "):
            if current_lines:
                sections.extend(_section_chunks(path, title, current_heading, current_lines))
            current_heading = _clean_heading(line)
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.extend(_section_chunks(path, title, current_heading, current_lines))

    return sections


def _section_chunks(
    path: Path,
    title: str,
    heading: str,
    lines: list[str],
) -> list[KnowledgeChunk]:
    body = "\n".join(lines).strip()
    if len(body) < MIN_CHUNK_LENGTH:
        return []

    source_path = str(path.relative_to(KNOWLEDGE_ROOT.parent.parent))
    heading_path = f"{title} > {heading}"
    chunk_text = f"# {title}\n\n## {heading}\n\n{body}".strip()
    return [
        KnowledgeChunk(
            source_path=source_path,
            heading=heading,
            heading_path=heading_path,
            topic_tags=_topic_tags(path.stem, heading, body),
            text=chunk_text,
        )
    ]


def _topic_tags(stem: str, heading: str, body: str) -> list[str]:
    candidates = {stem.replace("_", "-"), _slug(heading)}
    lower_body = body.casefold()
    for keyword in (
        "ids",
        "siem",
        "vulnerability-scanning",
        "web-application-security",
        "network-traffic-analysis",
        "incident-response",
        "soc",
        "penetration-testing",
        "database-management",
        "programming",
        "scripting",
        "career-path",
        "resume-improvement",
        "gap",
        "partial-match",
        "strength",
    ):
        if keyword.replace("-", " ") in lower_body or keyword in lower_body:
            candidates.add(keyword)
    return sorted(tag for tag in candidates if tag)


def _clean_heading(line: str) -> str:
    return line.lstrip("#").strip()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _content_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(value) for value in values) + "]"


def _excerpt(value: str, limit: int = 1200) -> str:
    return value if len(value) <= limit else value[: limit - 3].rstrip() + "..."
