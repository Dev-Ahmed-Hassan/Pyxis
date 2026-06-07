import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ResumeEvidenceSection = Literal[
    "skills_list",
    "project",
    "experience",
    "certification",
]
SkillExtractionSource = Literal["explicit", "inferred", "manual"]
SemanticEvidenceSection = Literal[
    "skills_list",
    "summary",
    "project",
    "experience",
    "education",
    "certification",
]


class MatchPreviewRequest(BaseModel):
    resume_id: uuid.UUID
    internship_id: uuid.UUID


class SemanticEmbeddingRefreshResponse(BaseModel):
    resume_id: uuid.UUID
    internship_id: uuid.UUID
    model_name: str
    resume_section_embedding_count: int
    internship_requirement_embedding_count: int


class MatchExplainabilityKnowledgeRefreshResponse(BaseModel):
    indexed: bool
    model_name: str | None
    source_file_count: int
    chunk_count: int
    warning: str | None = None


class MatchExplainabilityKnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1200)
    limit: int = Field(default=6, ge=1, le=10)


class MatchExplainabilityKnowledgeChunkResponse(BaseModel):
    id: uuid.UUID
    source_path: str
    heading: str
    heading_path: str
    topic_tags: list[str]
    chunk_text: str
    cosine_similarity: float


class MatchExplainabilityKnowledgeSearchResponse(BaseModel):
    query: str
    model_name: str | None
    chunks: list[MatchExplainabilityKnowledgeChunkResponse]
    warning: str | None = None


class ResumeSkillEvidence(BaseModel):
    skill: str
    section: ResumeEvidenceSection
    extraction_source: SkillExtractionSource
    confidence: float
    provenance_weight: float
    context: str | None


class MatchedSkillEvidence(BaseModel):
    requirement: str
    strongest_evidence: ResumeSkillEvidence


class SkillSectionScore(BaseModel):
    applied_weight: float
    coverage_percentage: float
    matched_skills: list[str]
    missing_skills: list[str]
    matched_skill_evidence: list[MatchedSkillEvidence]


class RequirementCategoryScore(BaseModel):
    contributes_to_score: bool
    required: SkillSectionScore
    preferred: SkillSectionScore


class RelatedSkillEvidence(BaseModel):
    resume_skill: str
    resume_evidence: ResumeSkillEvidence
    supported_requirement: str
    requirement_category: Literal[
        "required_skill",
        "preferred_skill",
        "required_domain_concept",
        "preferred_domain_concept",
    ]
    relationship: Literal["supports"]
    source: Literal["curated_rule", "neo4j"]
    support_path: list[str]
    relationship_path: list["RelatedSkillRelationshipStep"]
    path_distance: int
    path_confidence: float
    distance_decay: float
    relationship_credit_factor: float
    effective_credit_factor: float


class RelatedSkillRelationshipStep(BaseModel):
    evidence: str
    supported_requirement: str
    relationship_type: Literal[
        "alias_of",
        "evidence_for",
        "related_to",
        "prerequisite_for",
    ]
    confidence: float


class RelatedRequirementCredit(BaseModel):
    requirement: str
    requirement_category: Literal["required_skill", "preferred_skill"]
    credit_factor: float
    contribution_points: float
    strongest_evidence_path: list[str]
    strongest_resume_evidence: ResumeSkillEvidence


class RelatedSkillScore(BaseModel):
    maximum_credit_factor: float
    distance_decay_factor: float
    required_coverage_percentage: float
    preferred_coverage_percentage: float
    contribution_points: float
    supported_required_skills: list[str]
    supported_preferred_skills: list[str]
    requirement_credits: list[RelatedRequirementCredit]


class SemanticSkillEvidence(BaseModel):
    requirement: str
    requirement_category: Literal["required_skill", "preferred_skill"]
    resume_section: SemanticEvidenceSection
    resume_section_key: str
    resume_text_excerpt: str
    cosine_similarity: float
    threshold: float
    source: Literal["pgvector"]


class SemanticSkillScore(BaseModel):
    available: bool
    contributes_to_score: bool
    model_name: str | None
    reporting_threshold: float
    evidence: list[SemanticSkillEvidence]
    warnings: list[str]


class LlmRetrievedEvidence(BaseModel):
    requirement: str
    requirement_category: Literal["required_skill", "preferred_skill"]
    resume_section: SemanticEvidenceSection
    resume_section_key: str
    resume_text_excerpt: str
    cosine_similarity: float | None
    source: Literal["pgvector", "structured_resume_fallback"]


class LlmRequirementJudgment(BaseModel):
    requirement: str
    requirement_category: Literal["required_skill", "preferred_skill"]
    support_level: Literal["direct", "strong_partial", "weak_related", "absent"]
    confidence: float
    cited_resume_section_keys: list[str]
    reason: str


class LlmRequirementCredit(BaseModel):
    requirement: str
    requirement_category: Literal["required_skill", "preferred_skill"]
    support_level: Literal["direct", "strong_partial", "weak_related", "absent"]
    credit_factor: float
    contribution_points: float


class LlmFairnessAudit(BaseModel):
    assessment: Literal[
        "fair",
        "potentially_underestimated",
        "potentially_overestimated",
        "needs_manual_review",
    ]
    reason: str
    review_requirements: list[str]


class MatchLlmAdjudicationCreate(MatchPreviewRequest):
    pass


class MatchLlmAdjudicationResponse(BaseModel):
    id: uuid.UUID
    adjudication_version: str
    prompt_version: str
    score_version: str
    resume_id: uuid.UUID
    internship_id: uuid.UUID
    official_score: float
    shadow_score: float
    shadow_contribution_points: float
    contributes_to_official_score: bool
    provider: str
    model_name: str
    retrieved_evidence: list[LlmRetrievedEvidence]
    requirement_judgments: list[LlmRequirementJudgment]
    requirement_credits: list[LlmRequirementCredit]
    fairness_audit: LlmFairnessAudit
    created_at: datetime
    stale_at: datetime | None


class MatchPreviewResponse(BaseModel):
    score_version: str
    resume_id: uuid.UUID
    internship_id: uuid.UUID
    overall_score: float
    exact_overlap_score: float
    related_skill_score: RelatedSkillScore
    semantic_skill_score: SemanticSkillScore
    resume_skills: list[str]
    resume_skill_evidence: list[ResumeSkillEvidence]
    technical_skills: RequirementCategoryScore
    domain_concepts: RequirementCategoryScore
    soft_skills: RequirementCategoryScore
    related_skill_evidence: list[RelatedSkillEvidence]
    warnings: list[str]


class MatchAnalysisCreate(MatchPreviewRequest):
    analysis_session_id: uuid.UUID | None = None


class MatchAnalysisResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    internship_input_id: uuid.UUID
    analysis_session_id: uuid.UUID
    score_version: str
    overall_score: float
    created_at: datetime
    stale_at: datetime | None
    match: MatchPreviewResponse


class MatchLearningPathStep(BaseModel):
    order: int
    skill: str
    already_known: bool


class MatchLearningPathItem(BaseModel):
    target_skill: str
    requirement_category: Literal["required_skill", "preferred_skill"]
    priority: Literal["high", "medium"]
    status: Literal[
        "prerequisite_path_found",
        "foundation_detected",
        "direct_learning_required",
    ]
    current_foundation: str | None
    steps: list[MatchLearningPathStep]
    path_confidence: float | None
    source: Literal["neo4j", "local_dataset", "none"]
    relationship_types: list[
        Literal["evidence_for", "related_to", "prerequisite_for"]
    ]
    reason: str


class MatchLearningPathsResponse(BaseModel):
    analysis_id: uuid.UUID
    resume_id: uuid.UUID
    internship_id: uuid.UUID
    version: str
    existing_skills: list[str]
    missing_required_skills: list[str]
    missing_preferred_skills: list[str]
    learning_paths: list[MatchLearningPathItem]
    warnings: list[str]


MatchExplanationVerdict = Literal[
    "strong_match",
    "good_match",
    "moderate_match",
    "weak_match",
    "low_match",
]
ExplanationImpact = Literal["high", "medium", "low"]
ExplanationConfidence = Literal["high", "medium", "low"]
GapSeverity = Literal["high", "medium", "low"]
ResumeImprovementType = Literal[
    "clarify_existing_project",
    "add_missing_detail",
    "move_skill_into_project",
    "add_learning_project",
    "add_certification_context",
    "no_action_needed",
]


class MatchExplanationCreate(BaseModel):
    analysis_id: uuid.UUID
    adjudication_id: uuid.UUID | None = None


class MatchExplanationScoreCard(BaseModel):
    base_score: float
    ai_reviewed_score: float | None
    adjustment_points: float | None
    verdict: MatchExplanationVerdict
    headline: str
    summary: str


class MatchExplanationStrength(BaseModel):
    requirement: str
    title: str
    impact: ExplanationImpact
    evidence_section_keys: list[str]
    explanation: str
    confidence: ExplanationConfidence


class MatchExplanationPartialMatch(BaseModel):
    requirement: str
    title: str
    support_level: Literal["strong_partial", "weak_related"]
    evidence_section_keys: list[str]
    explanation: str
    missing_detail: str
    confidence: ExplanationConfidence


class MatchExplanationGap(BaseModel):
    requirement: str
    severity: GapSeverity
    reason: str
    why_it_matters: str
    recommended_action: str


class MatchExplanationResumeImprovement(BaseModel):
    type: ResumeImprovementType
    requirement: str
    suggestion: str
    why_it_matters: str
    evidence_section_keys: list[str]


class MatchExplanationLearningProject(BaseModel):
    requirement: str
    title: str
    goal: str
    tools: list[str]
    steps: list[str]
    resume_outcome: str


class MatchExplanationInterviewTalkingPoint(BaseModel):
    requirement: str
    prompt: str
    evidence_section_keys: list[str]


class MatchExplanationFairnessNote(BaseModel):
    assessment: Literal[
        "fair",
        "potentially_underestimated",
        "potentially_overestimated",
        "needs_manual_review",
    ]
    note: str
    related_requirements: list[str]


class MatchExplanationPayload(BaseModel):
    score_card: MatchExplanationScoreCard
    strengths: list[MatchExplanationStrength]
    partial_matches: list[MatchExplanationPartialMatch]
    gaps: list[MatchExplanationGap]
    resume_improvements: list[MatchExplanationResumeImprovement]
    learning_projects: list[MatchExplanationLearningProject]
    interview_talking_points: list[MatchExplanationInterviewTalkingPoint]
    fairness_notes: list[MatchExplanationFairnessNote]


class MatchExplanationResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    internship_input_id: uuid.UUID
    match_analysis_id: uuid.UUID
    match_llm_adjudication_id: uuid.UUID | None
    explanation_version: str
    prompt_version: str
    score_version: str
    provider: str
    model_name: str
    base_score: float
    ai_reviewed_score: float | None
    ai_adjustment_points: float | None
    retrieved_knowledge_chunks: list[MatchExplainabilityKnowledgeChunkResponse]
    explanation: MatchExplanationPayload
    created_at: datetime
    stale_at: datetime | None


GitHubEvidenceStrength = Literal["strong", "moderate", "weak"]
GitHubRequirementSupportLevel = Literal["direct", "partial", "adjacent", "none"]
GitHubActionPriority = Literal["high", "medium", "low"]


class GitHubMatchEvidenceCreate(BaseModel):
    match_analysis_id: uuid.UUID
    github_snapshot_id: uuid.UUID | None = None
    force_refresh: bool = False


class GitHubMatchedRepository(BaseModel):
    repository_name: str
    url: str | None
    evidence_strength: GitHubEvidenceStrength
    relevant_requirements: list[str]
    demonstrated_skills: list[str]
    why_it_supports_this_match: str
    application_use: str
    interview_use: str
    improvement_note: str


class GitHubRequirementSupport(BaseModel):
    requirement: str
    support_level: GitHubRequirementSupportLevel
    supporting_repositories: list[str]
    explanation: str
    remaining_gap: str


class GitHubMatchAction(BaseModel):
    title: str
    priority: GitHubActionPriority
    reason: str
    steps: list[str]


class GitHubInterviewQuestion(BaseModel):
    repository_name: str
    requirement: str
    question: str
    strong_answer_hint: str


class GitHubMatchEvidencePayload(BaseModel):
    headline: str
    summary: str
    overall_support_level: GitHubEvidenceStrength
    matched_repositories: list[GitHubMatchedRepository]
    requirement_support: list[GitHubRequirementSupport]
    application_talking_points: list[str]
    interview_questions: list[GitHubInterviewQuestion]
    improvement_actions: list[GitHubMatchAction]
    limitations: list[str]


class GitHubMatchEvidenceResponse(BaseModel):
    id: uuid.UUID
    match_analysis_id: uuid.UUID
    github_snapshot_id: uuid.UUID
    resume_id: uuid.UUID
    internship_input_id: uuid.UUID
    github_username: str
    evidence_version: str
    prompt_version: str
    provider: str
    model_name: str
    evidence_request: dict
    compact_context_used: dict
    evidence: GitHubMatchEvidencePayload
    created_at: datetime
    stale_at: datetime | None
