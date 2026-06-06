import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from api.auth import get_current_user
from database.postgres import get_db
from models.user import User
from schemas.career import (
    CareerRecommendationCreate,
    CareerRecommendationResponse,
    GraphCareerRecommendationsResponse,
)
from services.career_recommendation_service import (
    create_career_recommendation,
    get_career_recommendation,
)
from services.graph_career_service import get_graph_career_recommendations

router = APIRouter(prefix="/career", tags=["career"])


@router.get(
    "/graph-recommendations",
    response_model=GraphCareerRecommendationsResponse,
)
def get_graph_recommendations(
    limit: int = Query(default=8, ge=1, le=16),
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_graph_career_recommendations(
        database,
        current_user,
        limit=limit,
    )


@router.post(
    "/recommendations",
    response_model=CareerRecommendationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_recommendation(
    recommendation_create: CareerRecommendationCreate,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return create_career_recommendation(database, current_user, recommendation_create)


@router.get(
    "/recommendations/{recommendation_id}",
    response_model=CareerRecommendationResponse,
)
def get_recommendation(
    recommendation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_career_recommendation(database, current_user, recommendation_id)
