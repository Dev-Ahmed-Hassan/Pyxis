import type {
  StudentProfile,
  UserProfileFacts,
  UserProfileFactsRefresh,
} from '../types/profile'
import { apiRequest } from './api'

let cachedProfileFacts: UserProfileFacts | null = null
let cachedProfile: StudentProfile | null = null

export function getCachedStudentProfile() {
  return cachedProfile
}

export async function getStudentProfile() {
  const profile = await apiRequest<StudentProfile>('/profile')
  cachedProfile = profile
  return profile
}

export async function updateStudentProfile(input: {
  headline?: string | null
  bio?: string | null
  target_roles?: string[] | null
}) {
  const profile = await apiRequest<StudentProfile>('/profile', {
    method: 'PATCH',
    body: JSON.stringify(input),
  })
  cachedProfile = profile
  return profile
}

export function getCachedProfileFacts() {
  return cachedProfileFacts
}

export async function getProfileFacts() {
  const facts = await apiRequest<UserProfileFacts>('/profile/facts')
  cachedProfileFacts = facts
  return facts
}

export async function refreshProfileFacts() {
  const facts = await apiRequest<UserProfileFactsRefresh>(
    '/profile/facts/refresh',
    { method: 'POST' },
  )
  cachedProfileFacts = facts
  return facts
}
