import type {
  InterviewAnswerAcknowledgement,
  InterviewDifficulty,
  InterviewEvaluation,
  InterviewFocusArea,
  InterviewPreparation,
  InterviewSession,
  NextInterviewQuestion,
} from '../types/interview'
import { apiRequest } from './api'

type InterviewContextRequest = {
  matchAnalysisId: string
  matchExplanationId?: string | null
  githubEvidenceId?: string | null
  difficulty: InterviewDifficulty
  questionCount: number
  focusAreas: InterviewFocusArea[]
}

export function createInterviewPreparation(
  request: InterviewContextRequest,
  forceRefresh = false,
) {
  return apiRequest<InterviewPreparation>('/interviews/preparations', {
    method: 'POST',
    body: JSON.stringify({
      match_analysis_id: request.matchAnalysisId,
      match_explanation_id: request.matchExplanationId ?? null,
      github_evidence_id: request.githubEvidenceId ?? null,
      difficulty: request.difficulty,
      question_count: request.questionCount,
      focus_areas: request.focusAreas,
      force_refresh: forceRefresh,
    }),
  })
}

export function createInterviewSession(request: InterviewContextRequest) {
  return apiRequest<InterviewSession>('/interviews/sessions', {
    method: 'POST',
    body: JSON.stringify({
      match_analysis_id: request.matchAnalysisId,
      match_explanation_id: request.matchExplanationId ?? null,
      github_evidence_id: request.githubEvidenceId ?? null,
      difficulty: request.difficulty,
      question_count: request.questionCount,
      focus_areas: request.focusAreas,
    }),
  })
}

export function getNextInterviewQuestion(sessionId: string) {
  return apiRequest<NextInterviewQuestion>(
    `/interviews/sessions/${sessionId}/questions/next`,
    { method: 'POST' },
  )
}

export function submitInterviewAnswer(
  sessionId: string,
  questionId: string,
  answerText: string,
) {
  return apiRequest<InterviewAnswerAcknowledgement>(
    `/interviews/sessions/${sessionId}/answers`,
    {
      method: 'POST',
      body: JSON.stringify({
        question_id: questionId,
        answer_text: answerText,
      }),
    },
  )
}

export function completeInterviewSession(sessionId: string) {
  return apiRequest<InterviewEvaluation>(
    `/interviews/sessions/${sessionId}/complete`,
    { method: 'POST' },
  )
}
