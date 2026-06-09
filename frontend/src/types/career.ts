export type CareerFitLevel = 'strong' | 'good' | 'emerging' | 'explore_later'
export type CareerPriority = 'high' | 'medium' | 'low'

export type CareerPathRecommendation = {
  path: string
  fit_level: CareerFitLevel
  fit_score: number
  why_it_fits: string
  supporting_skills: string[]
  supporting_projects: string[]
  supporting_certifications: string[]
  missing_skills: string[]
  next_steps: string[]
  internship_titles_to_search: string[]
}

export type CareerRecommendation = {
  id: string
  recommendation_version: string
  prompt_version: string
  provider: string
  model_name: string
  target_field: string | null
  preferred_roles: string[]
  profile_snapshot: Record<string, unknown>
  retrieved_knowledge_chunks: Array<Record<string, unknown>>
  recommendation: {
    headline: string
    summary: string
    primary_paths: CareerPathRecommendation[]
    secondary_paths: CareerPathRecommendation[]
    paths_to_delay: CareerPathRecommendation[]
    profile_strengths: string[]
    skill_gaps: Array<{
      skill: string
      priority: CareerPriority
      related_paths: string[]
      why_it_matters: string
      suggested_action: string
    }>
    recommended_projects: Array<{
      title: string
      target_paths: string[]
      goal: string
      tools: string[]
      steps: string[]
      resume_outcome: string
    }>
    learning_roadmap: Array<{
      order: number
      title: string
      focus: string
      actions: string[]
      expected_outcome: string
    }>
    internship_search_terms: string[]
  }
  created_at: string
  stale_at: string | null
}

export type GraphCareerRecommendation = {
  role: string
  description: string
  domain: string
  fit_score: number
  fit_level: CareerFitLevel
  exact_required_coverage: number
  matched_skills: string[]
  related_skill_support: Array<{
    requirement: string
    supporting_skill: string
    support_path: string[]
    credit_factor: number
  }>
  missing_required_skills: string[]
  missing_preferred_skills: string[]
  learning_gaps: Array<{
    skill: string
    importance: 'required' | 'preferred'
    path_from_skill: string | null
    learning_steps: Array<{
      order: number
      skill: string
      already_known: boolean
    }>
  }>
}

export type GraphCareerRecommendations = {
  version: string
  user_id: string
  profile_skill_count: number
  graph_source: 'neo4j' | 'local_dataset'
  recommendations: GraphCareerRecommendation[]
  warnings: string[]
}
