export type ProfileSkillStrength = 'strong' | 'moderate' | 'emerging'

export type StudentProfile = {
  user_id: string
  headline: string | null
  bio: string | null
  target_roles: string[]
}

export type UserProfileSkillInventoryItem = {
  canonical_name: string
  display_name: string
  strength: ProfileSkillStrength
  source_count: number
  resume_ids: string[]
  source_sections: Array<'skills_list' | 'project' | 'experience' | 'certification'>
  best_confidence: number
  best_evidence: string | null
}

export type UserProfileProjectSource = {
  id: string
  resume_id: string
  source_key: string
  project_name: string | null
  description: string[]
  skills: string[]
  confidence: number
  evidence: string | null
  created_at: string
}

export type UserProfileCertificationSource = {
  id: string
  resume_id: string
  source_key: string
  certification_name: string
  issuer: string | null
  date: string | null
  confidence: number
  evidence: string | null
  created_at: string
}

export type UserProfileFacts = {
  user_id: string
  skill_inventory: UserProfileSkillInventoryItem[]
  skill_sources: Array<{
    id: string
    resume_id: string
    skill_name: string
    canonical_name: string
    source_section: 'skills_list' | 'project' | 'experience' | 'certification'
    source_key: string
    extraction_source: 'explicit' | 'inferred' | 'manual'
    confidence: number
    evidence: string | null
    context: string | null
    created_at: string
  }>
  project_sources: UserProfileProjectSource[]
  certification_sources: UserProfileCertificationSource[]
}

export type UserProfileFactsRefresh = UserProfileFacts & {
  refreshed_resume_count: number
  skill_source_count: number
  project_source_count: number
  certification_source_count: number
}
