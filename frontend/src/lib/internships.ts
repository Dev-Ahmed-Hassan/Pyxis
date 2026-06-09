import type {
  Internship,
  ParsedInternshipRequirements,
} from '../types/internship'
import { apiRequest } from './api'

let cachedInternships: Internship[] | null = null
let internshipListRequest: Promise<Internship[]> | null = null

export function getCachedInternships() {
  return cachedInternships
}

export function loadInternships(force = false) {
  if (cachedInternships && !force) {
    return Promise.resolve(cachedInternships)
  }

  if (!internshipListRequest) {
    internshipListRequest = apiRequest<Internship[]>('/internships')
      .then((internships) => {
        cachedInternships = internships
        return internships
      })
      .finally(() => {
        internshipListRequest = null
      })
  }

  return internshipListRequest
}

export async function createInternship(input: {
  label: string
  original_description: string
  application_url: string | null
}) {
  const internship = await apiRequest<Internship>('/internships', {
    method: 'POST',
    body: JSON.stringify(input),
  })
  cachedInternships = [internship, ...(cachedInternships ?? [])]
  return internship
}

export async function retryInternship(internshipId: string) {
  return updateInternshipFromAction(internshipId, 'retry')
}

export async function reparseInternship(internshipId: string) {
  return updateInternshipFromAction(internshipId, 'reparse')
}

async function updateInternshipFromAction(
  internshipId: string,
  action: 'retry' | 'reparse',
) {
  const internship = await apiRequest<Internship>(
    `/internships/${internshipId}/${action}`,
    { method: 'POST' },
  )
  cachedInternships =
    cachedInternships?.map((item) =>
      item.id === internship.id ? internship : item,
    ) ?? null
  return internship
}

export async function deleteInternship(internshipId: string) {
  await apiRequest<void>(`/internships/${internshipId}`, { method: 'DELETE' })
  cachedInternships =
    cachedInternships?.filter((item) => item.id !== internshipId) ?? null
}

export function getInternship(internshipId: string) {
  return apiRequest<Internship>(`/internships/${internshipId}`)
}

export function getParsedInternshipRequirements(internshipId: string) {
  return apiRequest<ParsedInternshipRequirements>(
    `/internships/${internshipId}/parsed-requirements`,
  )
}
