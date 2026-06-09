export type InterviewDifficulty = 'beginner' | 'intermediate' | 'advanced'

export type InterviewFocusArea =
  | 'technical'
  | 'resume'
  | 'behavioral'
  | 'situational'
  | 'github'

export type InterviewQuestionCategory =
  | 'role_technical'
  | 'resume_project'
  | 'experience'
  | 'gap_validation'
  | 'behavioral'
  | 'situational'
  | 'github_project'

export type InterviewPreparationQuestion = {
  category: InterviewQuestionCategory
  question_text: string
  why_relevant: string
  answer_structure: string
  grounded_evidence: string[]
  common_mistakes: string[]
  follow_up_questions: string[]
}

export type InterviewPreparation = {
  id: string
  match_analysis_id: string
  match_explanation_id: string | null
  github_evidence_id: string | null
  provider: string
  model_name: string
  preparation_payload: {
    interview_overview: string
    likely_focus: string
    questions: InterviewPreparationQuestion[]
    preparation_checklist: string[]
  }
  created_at: string
  stale_at: string | null
}

export type InterviewSession = {
  id: string
  match_analysis_id: string
  match_explanation_id: string | null
  github_evidence_id: string | null
  status: 'created' | 'in_progress' | 'completed' | 'abandoned'
  difficulty: InterviewDifficulty
  question_target: number
  focus_areas: string[]
  current_question_number: number
  provider: string
  model_name: string
  created_at: string
  started_at: string | null
  completed_at: string | null
  stale_at: string | null
}

export type InterviewQuestion = {
  id: string
  session_id: string
  sequence_number: number
  category: InterviewQuestionCategory
  question_text: string
  reason: string
  is_follow_up: boolean
  parent_question_id: string | null
  created_at: string
}

export type NextInterviewQuestion = {
  question: InterviewQuestion
  is_follow_up: boolean
  questions_remaining: number
}

export type InterviewAnswerAcknowledgement = {
  answer_id: string
  session_id: string
  next_is_follow_up: boolean
  session_complete: boolean
}

export type InterviewEvaluation = {
  id: string
  session_id: string
  provider: string
  model_name: string
  evaluation: {
    overall_score: number
    verdict: string
    summary: string
    category_scores: Array<{
      category: string
      score: number
      strengths: string[]
      improvements: string[]
    }>
    question_reviews: Array<{
      question_id: string
      question: string
      answer_summary: string
      score: number
      what_went_well: string[]
      what_was_missing: string[]
      better_answer_approach: string
    }>
    demonstrated_strengths: string[]
    knowledge_gaps: string[]
    communication_feedback: string[]
    unsupported_claims: string[]
    recommended_revision_topics: string[]
    next_actions: string[]
  }
  created_at: string
}
