export type GitHubCompactRepository = {
  name: string
  full_name: string | null
  html_url: string | null
  description: string | null
  topics: string[]
  primary_language: string | null
  languages: Record<string, number>
  stars: number
  forks: number
  watchers: number
  open_issues: number
  size: number
  default_branch: string | null
  created_at: string | null
  updated_at: string | null
  pushed_at: string | null
  is_fork: boolean
  is_archived: boolean
  has_readme: boolean
  readme_size: number | null
  readme_html_url: string | null
  readme_excerpt: string | null
}

export type GitHubCompactSnapshot = {
  profile?: {
    login?: string | null
    name?: string | null
    bio?: string | null
    company?: string | null
    blog?: string | null
    location?: string | null
    email?: string | null
    html_url?: string | null
    avatar_url?: string | null
    public_repos?: number | null
    followers?: number | null
    following?: number | null
    created_at?: string | null
    updated_at?: string | null
  }
  summary?: {
    repository_count?: number
    analyzed_repository_count?: number
    repositories_with_readme_count?: number
    repositories_with_description_count?: number
    total_stars?: number
    total_forks?: number
    top_languages?: string[]
  }
  language_totals?: Record<string, number>
  repositories?: GitHubCompactRepository[]
}

export type GitHubProfileSnapshot = {
  id: string
  github_username: string
  profile_payload: Record<string, unknown>
  repositories_payload: Array<Record<string, unknown>>
  languages_payload: Record<string, Record<string, unknown>>
  readmes_payload: Record<string, Record<string, unknown> | null>
  compact_snapshot: GitHubCompactSnapshot
  repository_limit: number
  fetched_at: string
  created_at: string
}

export type GitHubCompactSnapshotResponse = {
  id: string
  github_username: string
  compact_snapshot: GitHubCompactSnapshot
  repository_limit: number
  fetched_at: string
  created_at: string
}

export type GitHubRepositoryHighlight = {
  repository_name: string
  url: string | null
  evidence_level: string
  why_it_matters: string
  demonstrated_skills: string[]
  resume_bullet_suggestion: string
  improvement_note: string
}

export type GitHubProfileAnalysis = {
  id: string
  snapshot_id: string
  github_username: string
  analysis_version: string
  prompt_version: string
  provider: string
  model_name: string
  analysis_request: Record<string, unknown>
  compact_snapshot_used: GitHubCompactSnapshot
  analysis: {
    portfolio_score: number
    headline: string
    summary: string
    technology_summary: {
      top_languages: string[]
      detected_frameworks_or_tools: string[]
      likely_skill_areas: string[]
      evidence_notes: string[]
    }
    strong_repositories: GitHubRepositoryHighlight[]
    resume_worthy_projects: GitHubRepositoryHighlight[]
    weak_repositories: Array<{
      repository_name: string
      issue: string
      impact: string
      suggested_fix: string
      priority: string
    }>
    readme_improvements: Array<{
      repository_name: string
      current_problem: string
      recommended_sections: string[]
      example_summary: string
    }>
    career_alignment: Array<{
      role_or_field: string
      alignment_level: string
      supporting_repositories: string[]
      missing_evidence: string[]
      next_project_idea: string
    }>
    recommended_actions: Array<{
      title: string
      priority: string
      reason: string
      steps: string[]
    }>
    profile_presentation_issues: string[]
  }
  created_at: string
  stale_at: string | null
}
