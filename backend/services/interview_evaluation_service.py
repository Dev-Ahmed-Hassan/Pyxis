"""
Interview Evaluation Service.

Handles the completion of a Live Mode interview session and the generation
of the final collective evaluation report card (Section 7 of handoff).
"""

import json
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.interview_answer import InterviewAnswer
from models.interview_evaluation import InterviewEvaluation
from models.interview_question import InterviewQuestion
from models.interview_session import InterviewSession
from schemas.interview import InterviewEvaluationResponse
from services.ai.config import get_interview_routes
from services.ai.interview_schemas import FinalEvaluationOutput
from services.ai.orchestrator import AIOrchestratorError, generate_structured_with_fallback

EVALUATION_VERSION = 1
PROMPT_VERSION = 1


def complete_session(
    database: Session,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
) -> InterviewEvaluationResponse:
    """
    Completes the session if not already completed, and generates the final
    evaluation. If the evaluation already exists, returns it idempotently.
    """
    session = database.scalar(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        )
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    # Idempotent return if already evaluated
    if session.evaluation:
        return _to_response(session.evaluation)

    # Fetch all questions and answers to feed the final evaluator
    questions = database.scalars(
        select(InterviewQuestion)
        .where(InterviewQuestion.session_id == session.id)
        .order_by(InterviewQuestion.sequence_number.asc(), InterviewQuestion.created_at.asc())
    ).all()

    answers = database.scalars(
        select(InterviewAnswer).where(InterviewAnswer.session_id == session.id)
    ).all()
    
    # Map answers by question_id for easy association
    answer_map = {str(a.question_id): a for a in answers}

    if not answers:
        raise HTTPException(status_code=400, detail="Cannot evaluate a session with no answers.")

    # 1. Generate Final Evaluation via AI
    evaluation_output, provider, model_name = _run_final_evaluator(session, questions, answer_map)

    # 2. Mark session completed if it wasn't already
    if session.status != "completed":
        session.status = "completed"
        session.completed_at = datetime.now(timezone.utc)

    # 3. Save the evaluation
    evaluation_record = InterviewEvaluation(
        id=uuid.uuid4(),
        session_id=session.id,
        evaluation_version=EVALUATION_VERSION,
        prompt_version=PROMPT_VERSION,
        provider=provider,
        model_name=model_name,
        evaluation_payload=evaluation_output.model_dump(mode="json"),
        created_at=datetime.now(timezone.utc),
    )
    database.add(evaluation_record)
    database.commit()
    database.refresh(evaluation_record)

    return _to_response(evaluation_record)


def get_evaluation(
    database: Session,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
) -> InterviewEvaluationResponse:
    """
    Fetches the final evaluation for a completed session.
    """
    session = database.scalar(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        )
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    if not session.evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found for this session.")
        
    return _to_response(session.evaluation)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _run_final_evaluator(
    session: InterviewSession,
    questions: list[InterviewQuestion],
    answer_map: dict[str, InterviewAnswer],
) -> tuple[FinalEvaluationOutput, str, str]:
    
    # Build transcript
    transcript = []
    for q in questions:
        a = answer_map.get(str(q.id))
        if not a:
            continue
            
        transcript.append({
            "question_id": str(q.id),
            "category": q.category,
            "question": q.question_text,
            "candidate_answer": a.answer_text,
            "private_assessment": a.private_assessment,
        })

    prompt = f"""
You are the final interview evaluator. The interview is now complete.
Review the entire interview transcript, which includes the questions, the candidate's raw answers, and the private assessments calculated at each turn.

Generate a comprehensive final report card strictly following the required JSON schema.
Ensure that the `question_reviews` array contains exactly one review object for each question answered in the transcript.
Use the EXACT `question_id` string from the transcript for each review object.

Target Role/Focus: {", ".join(session.focus_areas)}

Transcript:
{json.dumps(transcript, indent=2)}
""".strip()

    try:
        output = generate_structured_with_fallback(
            routes=get_interview_routes(),
            prompt=prompt,
            json_schema=FinalEvaluationOutput.model_json_schema(),
        )
        return (
            FinalEvaluationOutput.model_validate(output.data),
            output.route.provider,
            output.route.model,
        )
    except (AIOrchestratorError, ValidationError) as error:
        raise HTTPException(status_code=503, detail=f"Final evaluation generation failed: {error}")


def _to_response(stored: InterviewEvaluation) -> InterviewEvaluationResponse:
    return InterviewEvaluationResponse(
        id=stored.id,
        session_id=stored.session_id,
        evaluation_version=stored.evaluation_version,
        prompt_version=stored.prompt_version,
        provider=stored.provider,
        model_name=stored.model_name,
        evaluation=stored.evaluation_payload,
        created_at=stored.created_at,
    )
