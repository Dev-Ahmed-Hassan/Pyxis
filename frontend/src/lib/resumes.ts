import type { ParsedResumeProfile, Resume } from '../types/resume'
import { apiRequest } from './api'

let cachedResumes: Resume[] | null = null
let resumeListRequest: Promise<Resume[]> | null = null

export function getCachedResumes() {
  return cachedResumes
}

export function loadResumes(force = false) {
  if (cachedResumes && !force) {
    return Promise.resolve(cachedResumes)
  }

  if (!resumeListRequest) {
    resumeListRequest = apiRequest<Resume[]>('/resumes')
      .then((resumes) => {
        cachedResumes = resumes
        return resumes
      })
      .finally(() => {
        resumeListRequest = null
      })
  }

  return resumeListRequest
}

export function clearResumeCache() {
  cachedResumes = null
}

export async function uploadResume(alias: string, file: File) {
  const formData = new FormData()
  formData.set('alias', alias)
  formData.set('uploaded_file', file)

  const resume = await apiRequest<Resume>('/resumes', {
    method: 'POST',
    body: formData,
  })
  cachedResumes = [resume, ...(cachedResumes ?? [])]
  return resume
}

export async function retryResume(resumeId: string) {
  const resumed = await apiRequest<Resume>(`/resumes/${resumeId}/retry`, {
    method: 'POST',
  })
  cachedResumes =
    cachedResumes?.map((resume) =>
      resume.id === resumed.id ? resumed : resume,
    ) ?? null
  return resumed
}

export function getResume(resumeId: string) {
  return apiRequest<Resume>(`/resumes/${resumeId}`)
}

export function getParsedResumeProfile(resumeId: string) {
  return apiRequest<ParsedResumeProfile>(
    `/resumes/${resumeId}/parsed-profile`,
  )
}
