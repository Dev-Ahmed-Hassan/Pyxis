import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.auth import get_current_user
from database.postgres import get_db
from models.user import User
from schemas.github import (
    GitHubCompactSnapshotResponse,
    GitHubProfileAnalysisCreate,
    GitHubProfileAnalysisResponse,
    GitHubProfileSnapshotResponse,
    GitHubSnapshotCreate,
)
from services.github_analysis_service import (
    create_github_profile_analysis,
    get_github_profile_analysis,
    get_latest_github_profile_analysis,
)
from services.github_snapshot_service import (
    create_github_profile_snapshot,
    get_github_compact_snapshot,
    get_github_profile_snapshot,
    get_latest_github_compact_snapshot,
    get_latest_github_profile_snapshot,
)

router = APIRouter(prefix="/github", tags=["github"])


@router.post(
    "/snapshots",
    response_model=GitHubProfileSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_snapshot(
    snapshot_create: GitHubSnapshotCreate,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return create_github_profile_snapshot(database, current_user, snapshot_create)


@router.get(
    "/snapshots/latest",
    response_model=GitHubProfileSnapshotResponse,
)
def get_latest_snapshot(
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_latest_github_profile_snapshot(database, current_user)


@router.get(
    "/snapshots/latest/compact",
    response_model=GitHubCompactSnapshotResponse,
)
def get_latest_compact_snapshot(
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_latest_github_compact_snapshot(database, current_user)


@router.get(
    "/snapshots/{snapshot_id}",
    response_model=GitHubProfileSnapshotResponse,
)
def get_snapshot(
    snapshot_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_github_profile_snapshot(database, current_user, snapshot_id)


@router.get(
    "/snapshots/{snapshot_id}/compact",
    response_model=GitHubCompactSnapshotResponse,
)
def get_compact_snapshot(
    snapshot_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_github_compact_snapshot(database, current_user, snapshot_id)


@router.post(
    "/analyses",
    response_model=GitHubProfileAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_analysis(
    analysis_create: GitHubProfileAnalysisCreate,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return create_github_profile_analysis(database, current_user, analysis_create)


@router.get(
    "/analyses/latest",
    response_model=GitHubProfileAnalysisResponse,
)
def get_latest_analysis(
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_latest_github_profile_analysis(database, current_user)


@router.get(
    "/analyses/{analysis_id}",
    response_model=GitHubProfileAnalysisResponse,
)
def get_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_github_profile_analysis(database, current_user, analysis_id)
