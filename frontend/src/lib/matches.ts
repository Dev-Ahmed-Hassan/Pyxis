import type {
  MatchAdjudication,
  MatchAnalysis,
  MatchExplanation,
  MatchLearningPaths,
  MatchPreview,
} from '../types/match'
import { apiRequest } from './api'

let cachedAnalyses: MatchAnalysis[] | null = null
let analysesRequest: Promise<MatchAnalysis[]> | null = null

export function previewMatch(resumeId: string, internshipId: string) {
  return apiRequest<MatchPreview>('/matches/preview', {
    method: 'POST',
    body: JSON.stringify({
      resume_id: resumeId,
      internship_id: internshipId,
    }),
  })
}

export async function createMatchAnalysis(
  resumeId: string,
  internshipId: string,
) {
  const analysis = await apiRequest<MatchAnalysis>('/matches/analyses', {
    method: 'POST',
    body: JSON.stringify({
      resume_id: resumeId,
      internship_id: internshipId,
    }),
  })
  cachedAnalyses = [
    analysis,
    ...(cachedAnalyses ?? []).filter((item) => item.id !== analysis.id),
  ]
  return analysis
}

export async function loadMatchAnalyses(force = false) {
  if (cachedAnalyses && !force) return cachedAnalyses
  if (!analysesRequest) {
    analysesRequest = apiRequest<MatchAnalysis[]>('/matches/analyses')
      .then((analyses) => {
        cachedAnalyses = analyses
        return analyses
      })
      .finally(() => {
        analysesRequest = null
      })
  }
  return analysesRequest
}

export function createMatchAdjudication(
  resumeId: string,
  internshipId: string,
) {
  return apiRequest<MatchAdjudication>('/matches/adjudications', {
    method: 'POST',
    body: JSON.stringify({
      resume_id: resumeId,
      internship_id: internshipId,
    }),
  })
}

export function getMatchAdjudication(adjudicationId: string) {
  return apiRequest<MatchAdjudication>(
    `/matches/adjudications/${adjudicationId}`,
  )
}

export function createMatchExplanation(
  analysisId: string,
  adjudicationId: string | null,
) {
  return apiRequest<MatchExplanation>('/matches/explanations', {
    method: 'POST',
    body: JSON.stringify({
      analysis_id: analysisId,
      adjudication_id: adjudicationId,
    }),
  })
}

export function getMatchExplanation(explanationId: string) {
  return apiRequest<MatchExplanation>(
    `/matches/explanations/${explanationId}`,
  )
}

export function getMatchLearningPaths(analysisId: string) {
  return apiRequest<MatchLearningPaths>(
    `/matches/analyses/${analysisId}/learning-paths`,
  )
}

type GuidanceReferences = {
  adjudicationId: string
  explanationId: string
}

const GUIDANCE_KEY = 'pyxis_match_guidance_references'

export function getGuidanceReferences(
  analysisId: string,
): GuidanceReferences | null {
  try {
    const stored = JSON.parse(
      window.localStorage.getItem(GUIDANCE_KEY) || '{}',
    ) as Record<string, GuidanceReferences>
    return stored[analysisId] ?? null
  } catch {
    return null
  }
}

export function saveGuidanceReferences(
  analysisId: string,
  references: GuidanceReferences,
) {
  let stored: Record<string, GuidanceReferences>
  try {
    stored = JSON.parse(
      window.localStorage.getItem(GUIDANCE_KEY) || '{}',
    ) as Record<string, GuidanceReferences>
  } catch {
    stored = {}
  }
  stored[analysisId] = references
  window.localStorage.setItem(GUIDANCE_KEY, JSON.stringify(stored))
}
