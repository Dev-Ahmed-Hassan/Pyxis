export type ResumeProcessingStatus =
  | 'uploaded'
  | 'extracting_text'
  | 'text_extracted'
  | 'parsing'
  | 'validating'
  | 'embedding'
  | 'ready'
  | 'failed'

export type Resume = {
  id: string
  alias: string
  original_filename: string
  mime_type: string
  file_size_bytes: number
  processing_status: ResumeProcessingStatus
  processing_error: string | null
  processing_attempts: number
  processing_started_at: string | null
  processing_completed_at: string | null
  next_retry_at: string | null
  is_default: boolean
  created_at: string
  updated_at: string
}

export type ExtractedText = {
  value: string | null
  confidence: number
  evidence: string | null
}

export type ExtractedSkill = {
  name: string
  canonical_name: string | null
  confidence: number
  evidence: string | null
  source: 'explicit' | 'inferred' | 'manual'
}

export type ResumeExperience = {
  company: string | null
  role: string | null
  start_date: string | null
  end_date: string | null
  description: string[]
  skills: ExtractedSkill[]
  confidence: number
  evidence: string | null
}

export type ResumeProject = {
  name: string | null
  description: string[]
  skills: ExtractedSkill[]
  confidence: number
  evidence: string | null
}

export type ResumeEducation = {
  institution: string | null
  degree: string | null
  field_of_study: string | null
  start_date: string | null
  end_date: string | null
  confidence: number
  evidence: string | null
}

export type ResumeCertification = {
  name: string
  issuer: string | null
  date: string | null
  confidence: number
  evidence: string | null
}

export type ParsedResumeProfile = {
  parsed_resume: {
    full_name: ExtractedText
    email: ExtractedText
    phone: ExtractedText
    location: ExtractedText
    summary: ExtractedText
    skills: ExtractedSkill[]
    experience: ResumeExperience[]
    projects: ResumeProject[]
    education: ResumeEducation[]
    certifications: ResumeCertification[]
    review_warnings: Array<{
      field: string
      message: string
      evidence: string | null
    }>
  }
  field_provenance: Record<string, string>
  updated_at: string
}
