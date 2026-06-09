"""
Interview Context Service.

Builds and returns the compact_context dictionary used by ALL interview
AI calls (preparation, session plan, next question, assessment, evaluation).

Design rules (Section 4 of the handoff):
- Never send the raw resume or full internship text to the LLM.
- Pull data from existing services only — do not duplicate their query logic.
- Apply hard caps on every list to keep prompt size bounded and auditable.
- GitHub evidence is optional; the feature works without it.
- Store the exact compact context so every AI result is reproducible.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from models.github_match_evidence import GitHubMatchEvidence
from models.match_analysis import MatchAnalysis
from models.match_explanation import MatchExplanation
from models.user import User
from schemas.matching import (
    GitHubMatchEvidencePayload,
    MatchExplanationPayload,
    MatchPreviewResponse,
)
from schemas.profile import UserProfileFactsResponse
from services.user_profile_facts_service import get_user_profile_facts

# ---------------------------------------------------------------------------
# Hard caps — keeps LLM prompt size bounded (Section 4: "set hard limits")
# ---------------------------------------------------------------------------

MAX_REQUIREMENTS = 15
MAX_SKILLS = 20
MAX_PROJECTS = 3
MAX_EXPERIENCE = 3
MAX_CERTIFICATIONS = 5
MAX_MATCH_STRENGTHS = 5
MAX_RESUME_SECTION_KEYS = 10
MAX_GITHUB_REPOS = 5


def build_compact_context(
    database: Session,
    user: User,
    match_analysis_id: uuid.UUID,
    match_explanation_id: uuid.UUID | None,
    github_evidence_id: uuid.UUID | None,
    mode: str,
    difficulty: str,
    question_count: int,
    focus_areas: list[str],
) -> dict:
    """
    Fetch the owned match analysis, optional explanation, and optional GitHub
    evidence, then compress them into the compact context format defined in
    Section 4 of the handoff document.

    Raises HTTP 404 if the analysis does not belong to the user.
    Raises HTTP 409 if the analysis is stale.
    """
    # --- Step 1: Load required match analysis (enforces ownership) ----------
    analysis = _get_owned_analysis(database, user, match_analysis_id)
    match = MatchPreviewResponse.model_validate(analysis.analysis_payload)
    profile_facts = get_user_profile_facts(database, user)

    # --- Step 2: Load optional explanation (enforces ownership if provided) -
    explanation_payload: MatchExplanationPayload | None = None
    if match_explanation_id:
        explanation = _get_owned_explanation(
            database,
            user,
            match_explanation_id,
            analysis.id,
        )
        explanation_payload = MatchExplanationPayload.model_validate(
            explanation.explanation_payload
        )

    # --- Step 3: Load optional GitHub evidence (enforces ownership) ---------
    github_payload: GitHubMatchEvidencePayload | None = None
    if github_evidence_id:
        evidence = _get_owned_github_evidence(
            database,
            user,
            github_evidence_id,
            analysis.id,
        )
        github_payload = GitHubMatchEvidencePayload.model_validate(
            evidence.evidence_payload
        )

    # --- Step 4: Build and return the compact context dict ------------------
    return _assemble_compact_context(
        analysis=analysis,
        match=match,
        profile_facts=profile_facts,
        explanation=explanation_payload,
        github=github_payload,
        mode=mode,
        difficulty=difficulty,
        question_count=question_count,
        focus_areas=focus_areas,
    )


# ---------------------------------------------------------------------------
# Private helpers — ownership-safe DB queries
# ---------------------------------------------------------------------------


def _get_owned_analysis(
    database: Session,
    user: User,
    analysis_id: uuid.UUID,
) -> MatchAnalysis:
    analysis = database.scalar(
        select(MatchAnalysis).where(
            MatchAnalysis.id == analysis_id,
            MatchAnalysis.user_id == user.id,
        )
    )
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match analysis not found or does not belong to this user.",
        )
    if analysis.stale_at:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Match analysis is stale. Create a fresh analysis before generating interview content.",
        )
    return analysis


def _get_owned_explanation(
    database: Session,
    user: User,
    explanation_id: uuid.UUID,
    match_analysis_id: uuid.UUID,
) -> MatchExplanation:
    explanation = database.scalar(
        select(MatchExplanation).where(
            MatchExplanation.id == explanation_id,
            MatchExplanation.user_id == user.id,
            MatchExplanation.match_analysis_id == match_analysis_id,
            MatchExplanation.stale_at.is_(None),
        )
    )
    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Match explanation not found, is stale, or does not belong "
                "to the selected match analysis."
            ),
        )
    return explanation


def _get_owned_github_evidence(
    database: Session,
    user: User,
    evidence_id: uuid.UUID,
    match_analysis_id: uuid.UUID,
) -> GitHubMatchEvidence:
    evidence = database.scalar(
        select(GitHubMatchEvidence).where(
            GitHubMatchEvidence.id == evidence_id,
            GitHubMatchEvidence.user_id == user.id,
            GitHubMatchEvidence.match_analysis_id == match_analysis_id,
            GitHubMatchEvidence.stale_at.is_(None),
        )
    )
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "GitHub match evidence not found, is stale, or does not belong "
                "to the selected match analysis."
            ),
        )
    return evidence


# ---------------------------------------------------------------------------
# Context assembly — maps raw DB data to the compact format (Section 4)
# ---------------------------------------------------------------------------


def _assemble_compact_context(
    analysis: MatchAnalysis,
    match: MatchPreviewResponse,
    profile_facts: UserProfileFactsResponse,
    explanation: MatchExplanationPayload | None,
    github: GitHubMatchEvidencePayload | None,
    mode: str,
    difficulty: str,
    question_count: int,
    focus_areas: list[str],
) -> dict:
    return {
        "target": _build_target(analysis),
        "requirements": _build_requirements(match),
        "candidate": _build_candidate(match, profile_facts, analysis.resume_id),
        "evidence": _build_evidence(match, explanation, github),
        "interview_settings": {
            "mode": mode,
            "difficulty": difficulty,
            "question_count": question_count,
            "focus_areas": focus_areas,
        },
    }


def _build_target(analysis: MatchAnalysis) -> dict:
    """
    Extracts the internship role and company from the stored analysis payload.
    The internship label is a compact human-readable identifier.
    """
    payload = analysis.analysis_payload
    # The internship label is stored inside the match payload
    internship_label = str(analysis.internship_input_id)
    role = payload.get("internship_role") or "Software Engineering Intern"
    company = payload.get("internship_company") or None

    return {
        "role": role,
        "company": company,
        "internship_label": internship_label,
    }


def _build_requirements(match: MatchPreviewResponse) -> dict:
    """
    Extracts the matched, missing, and preferred requirements from the
    deterministic match result. Applies hard caps per Section 4.
    """
    required = match.technical_skills.required
    preferred = match.technical_skills.preferred

    return {
        "required": required.matched_skills[:MAX_REQUIREMENTS] + required.missing_skills[:MAX_REQUIREMENTS],
        "preferred": preferred.matched_skills[:MAX_REQUIREMENTS] + preferred.missing_skills[:MAX_REQUIREMENTS],
        "matched": required.matched_skills[:MAX_REQUIREMENTS],
        "partial": [
            credit.requirement
            for credit in match.related_skill_score.requirement_credits[:MAX_REQUIREMENTS]
        ],
        "missing": required.missing_skills[:MAX_REQUIREMENTS],
    }


def _build_candidate(
    match: MatchPreviewResponse,
    profile_facts: UserProfileFactsResponse,
    resume_id: uuid.UUID,
) -> dict:
    """
    Builds the candidate section from resume skills and evidence.
    Uses the semantic evidence section keys to identify which resume
    sections are most relevant to this internship.
    """
    skills = match.resume_skills[:MAX_SKILLS]

    projects = [
        {
            "source_key": project.source_key,
            "name": project.project_name,
            "description": project.description,
            "skills": project.skills[:MAX_SKILLS],
            "evidence": project.evidence,
        }
        for project in profile_facts.project_sources
        if project.resume_id == resume_id
    ][:MAX_PROJECTS]

    certifications = [
        {
            "source_key": certification.source_key,
            "name": certification.certification_name,
            "issuer": certification.issuer,
            "date": certification.date,
            "evidence": certification.evidence,
        }
        for certification in profile_facts.certification_sources
        if certification.resume_id == resume_id
    ][:MAX_CERTIFICATIONS]

    experience = []
    seen_experience = set()
    for source in profile_facts.skill_sources:
        if source.resume_id != resume_id or source.source_section != "experience":
            continue
        experience_key = source.context or source.source_key.split(":skill:", 1)[0]
        if experience_key in seen_experience:
            continue
        seen_experience.add(experience_key)
        related_sources = [
            candidate
            for candidate in profile_facts.skill_sources
            if candidate.resume_id == resume_id
            and candidate.source_section == "experience"
            and (candidate.context or candidate.source_key.split(":skill:", 1)[0])
            == experience_key
        ]
        experience.append(
            {
                "label": source.context or "Resume experience",
                "source_keys": [candidate.source_key for candidate in related_sources],
                "skills": list(
                    dict.fromkeys(
                        candidate.canonical_name for candidate in related_sources
                    )
                )[:MAX_SKILLS],
                "evidence": list(
                    dict.fromkeys(
                        candidate.evidence
                        for candidate in related_sources
                        if candidate.evidence
                    )
                )[:3],
            }
        )
        if len(experience) >= MAX_EXPERIENCE:
            break

    return {
        "summary": f"Candidate has {len(skills)} identified skills relevant to this role.",
        "skills": skills,
        "projects": projects,
        "experience": experience,
        "certifications": certifications,
    }


def _build_evidence(
    match: MatchPreviewResponse,
    explanation: MatchExplanationPayload | None,
    github: GitHubMatchEvidencePayload | None,
) -> dict:
    """
    Assembles the evidence section. Match strengths come from the explanation
    if available. Resume section keys come from the semantic evidence.
    GitHub repositories are only included if GitHub evidence was provided.
    """
    # Match strengths from explanation (preferred) or from matched skills (fallback)
    if explanation:
        match_strengths = [
            strength.title
            for strength in explanation.strengths[:MAX_MATCH_STRENGTHS]
        ]
    else:
        match_strengths = match.technical_skills.required.matched_skills[:MAX_MATCH_STRENGTHS]

    # Grounded resume section keys (where exactly in the resume the evidence lives)
    resume_section_keys = list(
        dict.fromkeys(
            ev.resume_section_key
            for ev in match.semantic_skill_score.evidence[:MAX_RESUME_SECTION_KEYS]
        )
    )

    # GitHub repositories (optional)
    github_repositories = []
    if github:
        github_repositories = [
            {
                "name": repo.repository_name,
                "url": repo.url,
                "evidence_strength": repo.evidence_strength,
                "relevant_requirements": repo.relevant_requirements[:5],
                "demonstrated_skills": repo.demonstrated_skills[:5],
                "interview_use": repo.interview_use,
            }
            for repo in github.matched_repositories[:MAX_GITHUB_REPOS]
        ]

    return {
        "match_strengths": match_strengths,
        "resume_section_keys": resume_section_keys,
        "github_repositories": github_repositories,
    }
