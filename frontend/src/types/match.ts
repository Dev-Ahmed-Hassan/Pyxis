export type ResumeSkillEvidence = {
  skill: string
  section: 'skills_list' | 'project' | 'experience' | 'certification'
  extraction_source: 'explicit' | 'inferred' | 'manual'
  confidence: number
  provenance_weight: number
  context: string | null
}

export type MatchedSkillEvidence = {
  requirement: string
  strongest_evidence: ResumeSkillEvidence
}

export type SkillSectionScore = {
  applied_weight: number
  coverage_percentage: number
  matched_skills: string[]
  missing_skills: string[]
  matched_skill_evidence: MatchedSkillEvidence[]
}

export type RequirementCategoryScore = {
  contributes_to_score: boolean
  required: SkillSectionScore
  preferred: SkillSectionScore
}

export type RelatedSkillEvidence = {
  resume_skill: string
  resume_evidence: ResumeSkillEvidence
  supported_requirement: string
  requirement_category:
    | 'required_skill'
    | 'preferred_skill'
    | 'required_domain_concept'
    | 'preferred_domain_concept'
  relationship: 'supports'
  source: 'curated_rule' | 'neo4j'
  support_path: string[]
  relationship_path: Array<{
    evidence: string
    supported_requirement: string
    relationship_type:
      | 'alias_of'
      | 'evidence_for'
      | 'related_to'
      | 'prerequisite_for'
    confidence: number
  }>
  path_distance: number
  path_confidence: number
  distance_decay: number
  relationship_credit_factor: number
  effective_credit_factor: number
}

export type SemanticSkillEvidence = {
  requirement: string
  requirement_category: 'required_skill' | 'preferred_skill'
  resume_section:
    | 'skills_list'
    | 'summary'
    | 'project'
    | 'experience'
    | 'education'
    | 'certification'
  resume_section_key: string
  resume_text_excerpt: string
  cosine_similarity: number
  threshold: number
  source: 'pgvector'
}

export type MatchPreview = {
  score_version: string
  resume_id: string
  internship_id: string
  overall_score: number
  exact_overlap_score: number
  related_skill_score: {
    maximum_credit_factor: number
    distance_decay_factor: number
    required_coverage_percentage: number
    preferred_coverage_percentage: number
    contribution_points: number
    supported_required_skills: string[]
    supported_preferred_skills: string[]
    requirement_credits: Array<{
      requirement: string
      requirement_category: 'required_skill' | 'preferred_skill'
      credit_factor: number
      contribution_points: number
      strongest_evidence_path: string[]
      strongest_resume_evidence: ResumeSkillEvidence
    }>
  }
  semantic_skill_score: {
    available: boolean
    contributes_to_score: boolean
    model_name: string | null
    reporting_threshold: number
    evidence: SemanticSkillEvidence[]
    warnings: string[]
  }
  resume_skills: string[]
  resume_skill_evidence: ResumeSkillEvidence[]
  technical_skills: RequirementCategoryScore
  domain_concepts: RequirementCategoryScore
  soft_skills: RequirementCategoryScore
  related_skill_evidence: RelatedSkillEvidence[]
  warnings: string[]
}

export type MatchAnalysis = {
  id: string
  resume_id: string
  internship_input_id: string
  analysis_session_id: string
  score_version: string
  overall_score: number
  created_at: string
  stale_at: string | null
  match: MatchPreview
}

export type MatchAdjudication = {
  id: string
  official_score: number
  shadow_score: number
  shadow_contribution_points: number
  contributes_to_official_score: boolean
  provider: string
  model_name: string
  requirement_judgments: Array<{
    requirement: string
    requirement_category: 'required_skill' | 'preferred_skill'
    support_level: 'direct' | 'strong_partial' | 'weak_related' | 'absent'
    confidence: number
    cited_resume_section_keys: string[]
    reason: string
  }>
  fairness_audit: {
    assessment:
      | 'fair'
      | 'potentially_underestimated'
      | 'potentially_overestimated'
      | 'needs_manual_review'
    reason: string
    review_requirements: string[]
  }
  created_at: string
  stale_at: string | null
}

export type MatchExplanation = {
  id: string
  match_analysis_id: string
  match_llm_adjudication_id: string | null
  base_score: number
  ai_reviewed_score: number | null
  ai_adjustment_points: number | null
  provider: string
  model_name: string
  explanation: {
    score_card: {
      base_score: number
      ai_reviewed_score: number | null
      adjustment_points: number | null
      verdict:
        | 'strong_match'
        | 'good_match'
        | 'moderate_match'
        | 'weak_match'
        | 'low_match'
      headline: string
      summary: string
    }
    strengths: Array<{
      requirement: string
      title: string
      impact: 'high' | 'medium' | 'low'
      evidence_section_keys: string[]
      explanation: string
      confidence: 'high' | 'medium' | 'low'
    }>
    partial_matches: Array<{
      requirement: string
      title: string
      support_level: 'strong_partial' | 'weak_related'
      evidence_section_keys: string[]
      explanation: string
      missing_detail: string
      confidence: 'high' | 'medium' | 'low'
    }>
    gaps: Array<{
      requirement: string
      severity: 'high' | 'medium' | 'low'
      reason: string
      why_it_matters: string
      recommended_action: string
    }>
    resume_improvements: Array<{
      type: string
      requirement: string
      suggestion: string
      why_it_matters: string
      evidence_section_keys: string[]
    }>
    learning_projects: Array<{
      requirement: string
      title: string
      goal: string
      tools: string[]
      steps: string[]
      resume_outcome: string
    }>
    interview_talking_points: Array<{
      requirement: string
      prompt: string
      evidence_section_keys: string[]
    }>
    fairness_notes: Array<{
      assessment: string
      note: string
      related_requirements: string[]
    }>
  }
  created_at: string
  stale_at: string | null
}

export type MatchLearningPaths = {
  analysis_id: string
  existing_skills: string[]
  missing_required_skills: string[]
  missing_preferred_skills: string[]
  learning_paths: Array<{
    target_skill: string
    requirement_category: 'required_skill' | 'preferred_skill'
    priority: 'high' | 'medium'
    status:
      | 'prerequisite_path_found'
      | 'foundation_detected'
      | 'direct_learning_required'
    current_foundation: string | null
    steps: Array<{
      order: number
      skill: string
      already_known: boolean
    }>
    path_confidence: number | null
    source: 'neo4j' | 'local_dataset' | 'none'
    relationship_types: Array<
      'evidence_for' | 'related_to' | 'prerequisite_for'
    >
    reason: string
  }>
  warnings: string[]
}
