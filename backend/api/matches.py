import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.auth import get_current_user
from database.postgres import get_db
from models.user import User
from schemas.matching import (
    GitHubMatchEvidenceCreate,
    GitHubMatchEvidenceResponse,
    MatchAnalysisCreate,
    MatchAnalysisResponse,
    MatchExplainabilityKnowledgeRefreshResponse,
    MatchExplainabilityKnowledgeSearchRequest,
    MatchExplainabilityKnowledgeSearchResponse,
    MatchExplanationCreate,
    MatchExplanationResponse,
    MatchLlmAdjudicationCreate,
    MatchLlmAdjudicationResponse,
    MatchLearningPathsResponse,
    MatchPreviewRequest,
    MatchPreviewResponse,
    SemanticEmbeddingRefreshResponse,
)
from services.github_match_evidence_service import (
    create_github_match_evidence,
    get_github_match_evidence,
    get_latest_github_match_evidence,
)
from services.match_analysis_service import (
    create_match_analysis,
    get_match_analysis,
    list_match_analyses,
)
from services.match_llm_adjudication_service import (
    create_match_llm_adjudication,
    get_match_llm_adjudication,
)
from services.match_explainability_knowledge_service import (
    refresh_match_explainability_knowledge_embeddings,
    search_match_explainability_knowledge,
)
from services.match_explanation_service import (
    create_match_explanation,
    get_match_explanation,
)
from services.matching_service import get_match_preview
from services.graph_learning_path_service import get_match_learning_paths
from services.semantic_embedding_refresh_service import refresh_match_embeddings

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post(
    "/github-evidence",
    response_model=GitHubMatchEvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_github_evidence(
    evidence_create: GitHubMatchEvidenceCreate,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return create_github_match_evidence(database, current_user, evidence_create)


@router.get(
    "/github-evidence/latest",
    response_model=GitHubMatchEvidenceResponse,
)
def get_latest_github_evidence(
    match_analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_latest_github_match_evidence(
        database,
        current_user,
        match_analysis_id,
    )


@router.get(
    "/github-evidence/{evidence_id}",
    response_model=GitHubMatchEvidenceResponse,
)
def get_github_evidence(
    evidence_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_github_match_evidence(database, current_user, evidence_id)


@router.post(
    "/adjudications",
    response_model=MatchLlmAdjudicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_adjudication(
    adjudication_create: MatchLlmAdjudicationCreate,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return create_match_llm_adjudication(database, current_user, adjudication_create)


@router.get(
    "/adjudications/{adjudication_id}",
    response_model=MatchLlmAdjudicationResponse,
)
def get_adjudication(
    adjudication_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_match_llm_adjudication(database, current_user, adjudication_id)


@router.post(
    "/embeddings/refresh",
    response_model=SemanticEmbeddingRefreshResponse,
)
def refresh_embeddings(
    match_request: MatchPreviewRequest,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return refresh_match_embeddings(
        database=database,
        user=current_user,
        resume_id=match_request.resume_id,
        internship_id=match_request.internship_id,
    )


@router.post(
    "/explainability/knowledge/embeddings/refresh",
    response_model=MatchExplainabilityKnowledgeRefreshResponse,
)
def refresh_explainability_knowledge_embeddings(
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return refresh_match_explainability_knowledge_embeddings(database)


@router.post(
    "/explainability/knowledge/search",
    response_model=MatchExplainabilityKnowledgeSearchResponse,
)
def search_explainability_knowledge(
    search_request: MatchExplainabilityKnowledgeSearchRequest,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return search_match_explainability_knowledge(
        database=database,
        query=search_request.query,
        limit=search_request.limit,
    )


@router.post(
    "/explanations",
    response_model=MatchExplanationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_explanation(
    explanation_create: MatchExplanationCreate,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return create_match_explanation(database, current_user, explanation_create)


@router.get(
    "/explanations/{explanation_id}",
    response_model=MatchExplanationResponse,
)
def get_explanation(
    explanation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_match_explanation(database, current_user, explanation_id)


@router.get("/analyses", response_model=list[MatchAnalysisResponse])
def get_analyses(
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return list_match_analyses(database, current_user)


@router.get(
    "/analyses/{analysis_id}/learning-paths",
    response_model=MatchLearningPathsResponse,
)
def get_analysis_learning_paths(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_match_learning_paths(database, current_user, analysis_id)


@router.post(
    "/analyses",
    response_model=MatchAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_analysis(
    analysis_create: MatchAnalysisCreate,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return create_match_analysis(database, current_user, analysis_create)


@router.get("/analyses/{analysis_id}", response_model=MatchAnalysisResponse)
def get_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_match_analysis(database, current_user, analysis_id)


@router.post("/preview", response_model=MatchPreviewResponse)
def preview_match(
    match_request: MatchPreviewRequest,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_match_preview(
        database=database,
        user=current_user,
        resume_id=match_request.resume_id,
        internship_id=match_request.internship_id,
    )
