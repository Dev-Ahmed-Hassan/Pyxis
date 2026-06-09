import type { ExtractedSkill, ExtractedText } from './resume'

export type InternshipProcessingStatus =
  | 'submitted'
  | 'parsing'
  | 'validating'
  | 'ready'
  | 'failed'

export type Internship = {
  id: string
  label: string
  application_url: string | null
  processing_status: InternshipProcessingStatus
  processing_error: string | null
  processing_attempts: number
  processing_started_at: string | null
  processing_completed_at: string | null
  next_retry_at: string | null
  created_at: string
  updated_at: string
}

export type ParsedInternshipRequirements = {
  parsed_internship: {
    title: ExtractedText
    company: ExtractedText
    location: ExtractedText
    experience_level: ExtractedText
    required_skills: ExtractedSkill[]
    preferred_skills: ExtractedSkill[]
    required_domain_concepts: ExtractedSkill[]
    preferred_domain_concepts: ExtractedSkill[]
    required_soft_skills: ExtractedSkill[]
    preferred_soft_skills: ExtractedSkill[]
    responsibilities: string[]
    qualifications: string[]
    review_warnings: Array<{
      field: string
      message: string
      evidence: string | null
    }>
  }
  updated_at: string
}
