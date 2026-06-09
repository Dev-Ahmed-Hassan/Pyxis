from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import uuid

from api.auth import get_current_user
from database.postgres import get_db
from models.user import User
from schemas.interview import (
    InterviewPreparationCreate,
    InterviewPreparationResponse,
    InterviewSessionCreate,
    InterviewSessionResponse,
    NextQuestionResponse,
    InterviewEvaluationResponse,
)
from services.interview_preparation_service import (
    create_interview_preparation,
    get_interview_preparation,
)
from services.interview_session_service import (
    create_session,
    get_session,
    get_next_question,
    submit_answer,
)
from services.interview_evaluation_service import (
    complete_session,
    get_evaluation,
)

router = APIRouter(prefix="/interviews", tags=["interviews"])


@router.post("/preparations", response_model=InterviewPreparationResponse)
def create_preparation(
    request: InterviewPreparationCreate,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return create_interview_preparation(database, current_user, request)


@router.get("/preparations/{preparation_id}", response_model=InterviewPreparationResponse)
def get_preparation(
    preparation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_interview_preparation(database, current_user, preparation_id)


# ---------------------------------------------------------------------------
# Sessions (Live Mode)
# ---------------------------------------------------------------------------


@router.post("/sessions", response_model=InterviewSessionResponse)
def create_interview_session(
    request: InterviewSessionCreate,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return create_session(database, current_user, request)


@router.get("/sessions/{session_id}", response_model=InterviewSessionResponse)
def get_interview_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_session(database, current_user, session_id)


@router.post("/sessions/{session_id}/questions/next", response_model=NextQuestionResponse)
def get_next_interview_question(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_next_question(database, current_user, session_id)


from schemas.interview import InterviewAnswerSubmit, InterviewAnswerAcknowledgement

@router.post("/sessions/{session_id}/answers", response_model=InterviewAnswerAcknowledgement)
def submit_interview_answer(
    session_id: uuid.UUID,
    request: InterviewAnswerSubmit,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return submit_answer(database, current_user, session_id, request)


@router.post("/sessions/{session_id}/complete", response_model=InterviewEvaluationResponse)
def complete_interview_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return complete_session(database, current_user.id, session_id)


@router.get("/sessions/{session_id}/evaluation", response_model=InterviewEvaluationResponse)
def get_interview_evaluation(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    database: Session = Depends(get_db),
):
    return get_evaluation(database, current_user.id, session_id)


