import type {
  CareerRecommendation,
  GraphCareerRecommendations,
} from '../types/career'
import { apiRequest } from './api'

let cachedGraphRecommendations: GraphCareerRecommendations | null = null
let cachedCareerRecommendation: CareerRecommendation | null = null

export function getCachedGraphCareerRecommendations() {
  return cachedGraphRecommendations
}

export function getCachedCareerRecommendation() {
  return cachedCareerRecommendation
}

export async function getGraphCareerRecommendations(limit = 8) {
  const recommendations = await apiRequest<GraphCareerRecommendations>(
    `/career/graph-recommendations?limit=${limit}`,
  )
  cachedGraphRecommendations = recommendations
  return recommendations
}

export async function createCareerRecommendation(input: {
  target_field?: string | null
  preferred_roles?: string[]
}) {
  const recommendation = await apiRequest<CareerRecommendation>(
    '/career/recommendations',
    {
      method: 'POST',
      body: JSON.stringify({
        target_field: input.target_field?.trim() || null,
        preferred_roles: input.preferred_roles ?? [],
      }),
    },
  )
  cachedCareerRecommendation = recommendation
  return recommendation
}
