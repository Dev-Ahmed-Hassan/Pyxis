import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import {
  AlertTriangle,
  Brain,
  BriefcaseBusiness,
  CheckCircle2,
  CircleDashed,
  FileText,
  GitCompareArrows,
  Hammer,
  Layers3,
  Mic2,
  Route,
  Scale,
  ShieldCheck,
  Target,
  type LucideIcon,
} from 'lucide-react'
import { DataDonut, EvidenceDisclosure } from '../components/DataVisuals'
import { ApiError } from '../lib/api'
import { getCachedInternships, loadInternships } from '../lib/internships'
import {
  createMatchAdjudication,
  createMatchAnalysis,
  createMatchExplanation,
  getGuidanceReferences,
  getMatchAdjudication,
  getMatchExplanation,
  getMatchLearningPaths,
  loadMatchAnalyses,
  previewMatch,
  saveGuidanceReferences,
} from '../lib/matches'
import { getCachedResumes, loadResumes } from '../lib/resumes'
import type { Internship } from '../types/internship'
import type {
  MatchAdjudication,
  MatchAnalysis,
  MatchExplanation,
  MatchLearningPaths,
  MatchPreview,
  RequirementCategoryScore,
} from '../types/match'
import type { Resume } from '../types/resume'
import './Matches.css'

export function MatchesPage() {
  const [resumes, setResumes] = useState<Resume[]>(
    () => getCachedResumes() ?? [],
  )
  const [internships, setInternships] = useState<Internship[]>(
    () => getCachedInternships() ?? [],
  )
  const [analyses, setAnalyses] = useState<MatchAnalysis[]>([])
  const [resumeId, setResumeId] = useState('')
  const [internshipId, setInternshipId] = useState('')
  const [match, setMatch] = useState<MatchPreview | null>(null)
  const [savedAnalysisId, setSavedAnalysisId] = useState<string | null>(null)
  const [adjudication, setAdjudication] =
    useState<MatchAdjudication | null>(null)
  const [explanation, setExplanation] = useState<MatchExplanation | null>(null)
  const [learningPaths, setLearningPaths] =
    useState<MatchLearningPaths | null>(null)
  const [loadingData, setLoadingData] = useState(true)
  const [matching, setMatching] = useState(false)
  const [saving, setSaving] = useState(false)
  const [generatingGuidance, setGeneratingGuidance] = useState(false)
  const [loadingGuidance, setLoadingGuidance] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    Promise.all([loadResumes(), loadInternships(), loadMatchAnalyses()])
      .then(([resumeList, internshipList, analysisList]) => {
        if (!active) return
        setResumes(resumeList)
        setInternships(internshipList)
        setAnalyses(analysisList)
      })
      .catch((requestError) => {
        if (active) setError(errorMessage(requestError))
      })
      .finally(() => {
        if (active) setLoadingData(false)
      })

    return () => {
      active = false
    }
  }, [])

  const readyResumes = useMemo(
    () => resumes.filter((resume) => resume.processing_status === 'ready'),
    [resumes],
  )
  const readyInternships = useMemo(
    () =>
      internships.filter(
        (internship) => internship.processing_status === 'ready',
      ),
    [internships],
  )

  async function runPreview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try {
      setMatching(true)
      setError('')
      setSavedAnalysisId(null)
      clearGuidance()
      setMatch(await previewMatch(resumeId, internshipId))
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setMatching(false)
    }
  }

  async function saveAnalysis() {
    try {
      setSaving(true)
      setError('')
      const analysis = await createMatchAnalysis(resumeId, internshipId)
      setAnalyses((current) => [
        analysis,
        ...current.filter((item) => item.id !== analysis.id),
      ])
      setMatch(analysis.match)
      setSavedAnalysisId(analysis.id)
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setSaving(false)
    }
  }

  async function reopenAnalysis(analysis: MatchAnalysis) {
    setResumeId(analysis.resume_id)
    setInternshipId(analysis.internship_input_id)
    setMatch(analysis.match)
    setSavedAnalysisId(analysis.id)
    clearGuidance()
    setError('')
    window.scrollTo({ top: 0, behavior: 'smooth' })

    const references = getGuidanceReferences(analysis.id)
    if (!references) return

    try {
      setLoadingGuidance(true)
      const [savedAdjudication, savedExplanation, paths] = await Promise.all([
        getMatchAdjudication(references.adjudicationId),
        getMatchExplanation(references.explanationId),
        getMatchLearningPaths(analysis.id),
      ])
      setAdjudication(savedAdjudication)
      setExplanation(savedExplanation)
      setLearningPaths(paths)
    } catch {
      // The saved analysis remains usable if older generated guidance is stale.
    } finally {
      setLoadingGuidance(false)
    }
  }

  async function generateGuidance() {
    if (!savedAnalysisId) return

    try {
      setGeneratingGuidance(true)
      setError('')
      const pathsPromise = getMatchLearningPaths(savedAnalysisId)
      const reviewed = await createMatchAdjudication(resumeId, internshipId)
      setAdjudication(reviewed)
      const explained = await createMatchExplanation(
        savedAnalysisId,
        reviewed.id,
      )
      const paths = await pathsPromise
      setExplanation(explained)
      setLearningPaths(paths)
      saveGuidanceReferences(savedAnalysisId, {
        adjudicationId: reviewed.id,
        explanationId: explained.id,
      })
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setGeneratingGuidance(false)
    }
  }

  function clearGuidance() {
    setAdjudication(null)
    setExplanation(null)
    setLearningPaths(null)
  }

  const selectedResume = resumes.find((item) => item.id === resumeId)
  const selectedInternship = internships.find(
    (item) => item.id === internshipId,
  )

  return (
    <main className="app-page matches-page match-redesign">
      <header className="app-page-header">
        <div>
          <span className="app-page-eyebrow">Evidence comparison</span>
          <h1>Match workspace</h1>
          <p>
            Compare a parsed resume with a parsed internship. Preview is
            deterministic and does not call the LLM adjudicator.
          </p>
        </div>
        <div className="match-page-signal" aria-hidden="true">
          <Layers3 size={18} />
          <span>{readyResumes.length} resumes</span>
          <i />
          <span>{readyInternships.length} roles</span>
        </div>
      </header>

      <form className="match-selector" onSubmit={runPreview}>
        <Selector
          disabled={loadingData}
          icon={FileText}
          label="Resume evidence"
          onChange={setResumeId}
          options={readyResumes.map((resume) => ({
            id: resume.id,
            label: resume.alias,
            note: `${resume.original_filename}${resume.is_default ? ' · Default' : ''}`,
          }))}
          placeholder={
            readyResumes.length ? 'Choose a ready resume' : 'No ready resumes'
          }
          value={resumeId}
        />
        <div className="match-selector-connector">
          <GitCompareArrows size={22} />
          <span>COMPARE</span>
        </div>
        <Selector
          disabled={loadingData}
          icon={BriefcaseBusiness}
          label="Internship requirements"
          onChange={setInternshipId}
          options={readyInternships.map((internship) => ({
            id: internship.id,
            label: internship.label,
            note: internship.application_url
              ? 'Application URL saved'
              : 'Saved role description',
          }))}
          placeholder={
            readyInternships.length
              ? 'Choose a ready internship'
              : 'No ready internships'
          }
          value={internshipId}
        />
        <div className="match-selector-action">
          <div>
            <span>{selectedResume?.alias || 'Resume not selected'}</span>
            <i>against</i>
            <span>{selectedInternship?.label || 'Internship not selected'}</span>
          </div>
          <button
            className="app-primary-action"
            disabled={matching || !resumeId || !internshipId}
            type="submit"
          >
            {matching ? 'Calculating match...' : 'Preview match'}
          </button>
        </div>
      </form>

      {error && <div className="match-error">{error}</div>}

      {match && (
        <MatchDashboard
          match={match}
          adjudication={adjudication}
          explanation={explanation}
          generatingGuidance={generatingGuidance}
          learningPaths={learningPaths}
          loadingGuidance={loadingGuidance}
          onGenerateGuidance={() => void generateGuidance()}
          onSave={() => void saveAnalysis()}
          savedAnalysisId={savedAnalysisId}
          saving={saving}
        />
      )}

      <section className="match-history">
        <header>
          <div>
            <span className="app-page-eyebrow">Saved analyses</span>
            <h2>Previous comparisons</h2>
          </div>
          <strong>{String(analyses.length).padStart(2, '0')}</strong>
        </header>
        {analyses.length === 0 ? (
          <div className="match-history-empty">
            <p>
              No saved comparisons yet. Choose a ready resume and internship,
              preview the match, then save it to unlock guidance and interview
              prep.
            </p>
            <div>
              <Link className="app-secondary-action" to="/resumes">
                Check resumes
              </Link>
              <Link className="app-secondary-action" to="/internships">
                Check internships
              </Link>
            </div>
          </div>
        ) : (
          <div>
            {analyses.map((analysis) => (
              <button
                key={analysis.id}
                onClick={() => void reopenAnalysis(analysis)}
                type="button"
              >
                <strong>{Math.round(analysis.overall_score)}%</strong>
                <span>
                  {resumeName(resumes, analysis.resume_id)}
                  <small>
                    {internshipName(
                      internships,
                      analysis.internship_input_id,
                    )}
                  </small>
                </span>
                <i>{formatDate(analysis.created_at)}</i>
                {analysis.stale_at && <em>Stale</em>}
              </button>
            ))}
          </div>
        )}
      </section>
    </main>
  )
}

function MatchDashboard({
  adjudication,
  explanation,
  generatingGuidance,
  learningPaths,
  loadingGuidance,
  match,
  onGenerateGuidance,
  onSave,
  savedAnalysisId,
  saving,
}: {
  adjudication: MatchAdjudication | null
  explanation: MatchExplanation | null
  generatingGuidance: boolean
  learningPaths: MatchLearningPaths | null
  loadingGuidance: boolean
  match: MatchPreview
  onGenerateGuidance: () => void
  onSave: () => void
  savedAnalysisId: string | null
  saving: boolean
}) {
  const requiredMatched =
    match.technical_skills.required.matched_skills.length +
    match.domain_concepts.required.matched_skills.length +
    match.soft_skills.required.matched_skills.length
  const requiredMissing =
    match.technical_skills.required.missing_skills.length +
    match.domain_concepts.required.missing_skills.length +
    match.soft_skills.required.missing_skills.length
  const preferredMatched =
    match.technical_skills.preferred.matched_skills.length +
    match.domain_concepts.preferred.matched_skills.length +
    match.soft_skills.preferred.matched_skills.length
  const preferredMissing =
    match.technical_skills.preferred.missing_skills.length +
    match.domain_concepts.preferred.missing_skills.length +
    match.soft_skills.preferred.missing_skills.length

  return (
    <section className="match-dashboard">
      <div className="match-state-strip" aria-label="Match workflow state">
        <span className="is-complete">
          <CheckCircle2 size={13} />
          Preview calculated
        </span>
        <span className={savedAnalysisId ? 'is-complete' : ''}>
          {savedAnalysisId ? <CheckCircle2 size={13} /> : <CircleDashed size={13} />}
          {savedAnalysisId ? 'Analysis saved' : 'Save to unlock guidance'}
        </span>
        <span className={explanation ? 'is-complete' : ''}>
          {explanation ? <CheckCircle2 size={13} /> : <CircleDashed size={13} />}
          {explanation ? 'AI guidance ready' : 'AI guidance optional'}
        </span>
      </div>

      <section className="match-guidance-gateway">
        <div>
          <span className="app-page-eyebrow">
            <Brain size={13} />
            Student-facing analysis
          </span>
          <h2>
            {explanation
              ? explanation.explanation.score_card.headline
              : 'Turn this score into practical guidance.'}
          </h2>
          <p>
            {explanation
              ? explanation.explanation.score_card.summary
              : 'AI review checks potentially missed evidence, explains the result, and turns gaps into resume actions, projects, interview points, and learning paths.'}
          </p>
        </div>
        {!explanation && (
          <div className="match-preview-score" aria-label="Preview score">
            <span>Preview</span>
            <strong>{Math.round(match.overall_score)}%</strong>
          </div>
        )}
        {!savedAnalysisId ? (
          <button
            className="app-primary-action"
            disabled={saving}
            onClick={onSave}
            type="button"
          >
            {saving ? 'Saving analysis...' : 'Save analysis to continue'}
          </button>
        ) : !explanation ? (
          <div className="match-guidance-action">
            <button
              className="app-primary-action"
              disabled={generatingGuidance || loadingGuidance}
              onClick={onGenerateGuidance}
              type="button"
            >
              {loadingGuidance
                ? 'Loading saved guidance...'
                : generatingGuidance
                  ? 'Generating guidance...'
                  : 'Generate AI guidance'}
            </button>
            <small>Uses AI credits and may take a moment.</small>
          </div>
        ) : (
          <div className="match-guidance-score">
            <span>AI-reviewed score</span>
            <strong>
              {Math.round(
                explanation.explanation.score_card.ai_reviewed_score ??
                  match.overall_score,
              )}
              %
            </strong>
            <small>
              Base {Math.round(match.overall_score)}%
              {explanation.ai_adjustment_points !== null
                ? ` · +${explanation.ai_adjustment_points.toFixed(1)} review`
                : ''}
            </small>
            <Link className="match-next-link" to="/interviews">
              Prepare for interview
            </Link>
          </div>
        )}
      </section>

      {explanation && (
        <GuidanceDashboard
          adjudication={adjudication}
          explanation={explanation}
          learningPaths={learningPaths}
        />
      )}

      <details className="match-technical-panel" open={!explanation}>
        <summary>
          <div>
            <span className="app-page-eyebrow">
              <Layers3 size={13} />
              How the score was calculated
            </span>
            <h2>Technical match evidence</h2>
            <p>
              Deterministic scoring, graph relationships, semantic retrieval,
              and warnings are preserved here for transparency.
            </p>
          </div>
          <strong>{Math.round(match.overall_score)}%</strong>
        </summary>

        <header className="match-score-hero">
          <div className="match-score-number">
            <span>Official score</span>
            <strong>{Math.round(match.overall_score)}%</strong>
            <small>{match.score_version}</small>
          </div>
          <div>
            <span className="app-page-eyebrow">
              <Target size={13} />
              Scoring composition
            </span>
            <h2>What produced this result</h2>
            <div className="match-score-parts">
              <div>
                <strong>{match.exact_overlap_score.toFixed(1)}</strong>
                <span>Exact overlap</span>
              </div>
              <div>
                <strong>
                  +{match.related_skill_score.contribution_points.toFixed(1)}
                </strong>
                <span>Related-skill credit</span>
              </div>
              <div>
                <strong>{match.semantic_skill_score.evidence.length}</strong>
                <span>
                  Semantic evidence
                  {!match.semantic_skill_score.contributes_to_score
                    ? ' · non-scoring'
                    : ''}
                </span>
              </div>
            </div>
            <button
              className="app-primary-action"
              disabled={saving || Boolean(savedAnalysisId)}
              onClick={onSave}
              type="button"
            >
              {savedAnalysisId
                ? 'Analysis saved'
                : saving
                  ? 'Saving...'
                  : 'Save this analysis'}
            </button>
          </div>
          <DataDonut
            data={[
              { name: 'Required matched', value: requiredMatched, color: '#315c52' },
              { name: 'Required missing', value: requiredMissing, color: '#bf7b73' },
              { name: 'Preferred matched', value: preferredMatched, color: '#9db7ae' },
              { name: 'Preferred missing', value: preferredMissing, color: '#d9ccb1' },
            ]}
            label="requirements"
            total={
              requiredMatched +
              requiredMissing +
              preferredMatched +
              preferredMissing
            }
          />
        </header>

        <div className="match-category-grid">
          <CategoryCard
            category={match.technical_skills}
            label="Technical skills"
          />
          <CategoryCard
            category={match.domain_concepts}
            label="Domain concepts"
          />
          <CategoryCard category={match.soft_skills} label="Soft skills" />
        </div>

        <EvidenceSection match={match} title="Exact evidence" type="exact" />
        <EvidenceSection
          match={match}
          title="Related-skill paths"
          type="related"
        />
        <EvidenceSection
          match={match}
          title="Semantic evidence"
          type="semantic"
        />

        {(match.warnings.length > 0 ||
          match.semantic_skill_score.warnings.length > 0) && (
          <section className="match-warning-panel">
            <span className="app-page-eyebrow">Scoring notes</span>
            {[...match.warnings, ...match.semantic_skill_score.warnings].map(
              (warning, index) => (
                <p key={`${warning}-${index}`}>{warning}</p>
              ),
            )}
          </section>
        )}
      </details>
    </section>
  )
}

function GuidanceDashboard({
  adjudication,
  explanation,
  learningPaths,
}: {
  adjudication: MatchAdjudication | null
  explanation: MatchExplanation
  learningPaths: MatchLearningPaths | null
}) {
  const content = explanation.explanation

  return (
    <div className="guidance-dashboard">
      <section className="guidance-summary-grid">
        <GuidanceList
          empty="No major strengths were returned."
          items={content.strengths.map((item) => ({
            title: item.title,
            label: `${item.impact} impact`,
            body: item.explanation,
          }))}
          icon={ShieldCheck}
          title="Why you match"
          tone="positive"
        />
        <GuidanceList
          empty="No partial evidence was identified."
          items={content.partial_matches.map((item) => ({
            title: item.title,
            label: item.support_level.replaceAll('_', ' '),
            body: `${item.explanation} ${item.missing_detail}`,
          }))}
          icon={Scale}
          title="Evidence that needs clarity"
          tone="partial"
        />
        <GuidanceList
          empty="No material gaps were returned."
          items={content.gaps.map((item) => ({
            title: item.requirement,
            label: `${item.severity} priority`,
            body: item.recommended_action,
          }))}
          icon={AlertTriangle}
          title="What to improve first"
          tone="gap"
        />
      </section>

      <section className="guidance-action-section">
        <header>
          <span className="app-page-eyebrow">
            <Hammer size={13} />
            Resume actions
          </span>
          <h2>Make the existing evidence easier to see</h2>
        </header>
        <div className="guidance-action-grid">
          {content.resume_improvements.map((item, index) => (
            <article key={`${item.requirement}-${index}`}>
              <span>{String(index + 1).padStart(2, '0')}</span>
              <h3>{item.requirement}</h3>
              <p>{item.suggestion}</p>
              <small>{item.why_it_matters}</small>
            </article>
          ))}
        </div>
      </section>

      <section className="guidance-projects">
        <header>
          <span className="app-page-eyebrow">
            <BriefcaseBusiness size={13} />
            Portfolio projects
          </span>
          <h2>Build evidence for the missing requirements</h2>
        </header>
        <div>
          {content.learning_projects.map((project, index) => (
            <article key={`${project.title}-${index}`}>
              <span>{project.requirement}</span>
              <h3>{project.title}</h3>
              <p>{project.goal}</p>
              <div>
                {project.tools.map((tool) => <small key={tool}>{tool}</small>)}
              </div>
              <ol>
                {project.steps.map((step, stepIndex) => (
                  <li key={`${step}-${stepIndex}`}>{step}</li>
                ))}
              </ol>
              <strong>Resume outcome: {project.resume_outcome}</strong>
            </article>
          ))}
        </div>
      </section>

      {learningPaths && learningPaths.learning_paths.length > 0 && (
        <section className="guidance-learning-paths">
          <header>
            <span className="app-page-eyebrow">
              <Route size={13} />
              Graph learning paths
            </span>
            <h2>Move from what you know to what the role needs</h2>
          </header>
          <div>
            {learningPaths.learning_paths.map((path) => (
              <article key={path.target_skill}>
                <div>
                  <span>{path.priority} priority</span>
                  <h3>{path.target_skill}</h3>
                  <p>{path.reason}</p>
                </div>
                <ol>
                  {path.steps.map((step) => (
                    <li
                      className={step.already_known ? 'is-known' : ''}
                      key={`${path.target_skill}-${step.order}`}
                    >
                      <span>{step.order}</span>
                      {step.skill}
                    </li>
                  ))}
                </ol>
              </article>
            ))}
          </div>
        </section>
      )}

      <section className="guidance-interview">
        <div>
          <span className="app-page-eyebrow">
            <Mic2 size={13} />
            Interview preparation
          </span>
          <h2>Talking points from your own evidence</h2>
        </div>
        <ol>
          {content.interview_talking_points.map((item, index) => (
            <li key={`${item.requirement}-${index}`}>
              <span>{item.requirement}</span>
              <p>{item.prompt}</p>
            </li>
          ))}
        </ol>
      </section>

      {adjudication && (
        <section className="guidance-fairness">
          <span className="app-page-eyebrow">
            <Scale size={13} />
            AI fairness review
          </span>
          <h2>{adjudication.fairness_audit.assessment.replaceAll('_', ' ')}</h2>
          <p>{adjudication.fairness_audit.reason}</p>
          <small>
            Reviewed by {adjudication.provider} / {adjudication.model_name}.
            The reviewed score does not overwrite the deterministic score.
          </small>
        </section>
      )}
    </div>
  )
}

function GuidanceList({
  empty,
  icon: Icon,
  items,
  title,
  tone,
}: {
  empty: string
  icon: LucideIcon
  items: Array<{ title: string; label: string; body: string }>
  title: string
  tone: 'positive' | 'partial' | 'gap'
}) {
  return (
    <section className={`guidance-list is-${tone}`}>
      <header>
        <h2><Icon size={18} />{title}</h2>
        <strong>{String(items.length).padStart(2, '0')}</strong>
      </header>
      {items.length === 0 ? (
        <p>{empty}</p>
      ) : (
        <div>
          {items.map((item, index) => (
            <article key={`${item.title}-${index}`}>
              <span>{item.label}</span>
              <h3>{item.title}</h3>
              <p>{item.body}</p>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}

function Selector({
  disabled,
  icon: Icon,
  label,
  onChange,
  options,
  placeholder,
  value,
}: {
  disabled: boolean
  icon: LucideIcon
  label: string
  onChange: (value: string) => void
  options: Array<{ id: string; label: string; note: string }>
  placeholder: string
  value: string
}) {
  return (
    <label className="match-select-field">
      <span><Icon size={15} />{label}</span>
      <select
        disabled={disabled || options.length === 0}
        onChange={(event) => onChange(event.target.value)}
        required
        value={value}
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.label} — {option.note}
          </option>
        ))}
      </select>
    </label>
  )
}

function CategoryCard({
  category,
  label,
}: {
  category: RequirementCategoryScore
  label: string
}) {
  return (
    <article className="match-category-card">
      <header>
        <div>
          <span>{label}</span>
          <small>
            {category.contributes_to_score
              ? 'Contributes to score'
              : 'Reported separately'}
          </small>
        </div>
      </header>
      <CoverageRow label="Required" score={category.required} />
      <CoverageRow label="Preferred" score={category.preferred} />
    </article>
  )
}

function CoverageRow({
  label,
  score,
}: {
  label: string
  score: RequirementCategoryScore['required']
}) {
  return (
    <div className="match-coverage-row">
      <div>
        <span>{label}</span>
        <strong>{Math.round(score.coverage_percentage)}%</strong>
      </div>
      <i><span style={{ width: `${score.coverage_percentage}%` }} /></i>
      <div className="match-chip-groups">
        <div>
          {score.matched_skills.map((skill) => (
            <span className="is-matched" key={skill}>{skill}</span>
          ))}
        </div>
        <div>
          {score.missing_skills.map((skill) => (
            <span className="is-missing" key={skill}>{skill}</span>
          ))}
        </div>
      </div>
    </div>
  )
}

function EvidenceSection({
  match,
  title,
  type,
}: {
  match: MatchPreview
  title: string
  type: 'exact' | 'related' | 'semantic'
}) {
  const exactEvidence = [
    match.technical_skills.required,
    match.technical_skills.preferred,
    match.domain_concepts.required,
    match.domain_concepts.preferred,
    match.soft_skills.required,
    match.soft_skills.preferred,
  ].flatMap((section) => section.matched_skill_evidence)
  const count =
    type === 'exact'
      ? exactEvidence.length
      : type === 'related'
        ? match.related_skill_evidence.length
        : match.semantic_skill_score.evidence.length

  return (
    <details className="match-evidence-section" open={type === 'exact'}>
      <summary>
        <div>
          <span className="app-page-eyebrow">Evidence layer</span>
          <h2>{title}</h2>
        </div>
        <strong>{String(count).padStart(2, '0')}</strong>
      </summary>

      {count === 0 ? (
        <p className="match-empty-evidence">No evidence was returned here.</p>
      ) : type === 'exact' ? (
        <div className="match-evidence-grid">
          {exactEvidence.map((evidence, index) => (
            <article key={`${evidence.requirement}-${index}`}>
              <h3>{evidence.requirement}</h3>
              <p>
                Matched by {evidence.strongest_evidence.skill} ·{' '}
                {evidence.strongest_evidence.section.replaceAll('_', ' ')}
              </p>
              <EvidenceDisclosure
                confidence={evidence.strongest_evidence.confidence}
                evidence={evidence.strongest_evidence.context}
                source={evidence.strongest_evidence.extraction_source}
              />
            </article>
          ))}
        </div>
      ) : type === 'related' ? (
        <div className="match-related-list">
          {match.related_skill_evidence.map((evidence, index) => (
            <article key={`${evidence.supported_requirement}-${index}`}>
              <div>
                <strong>{evidence.resume_skill}</strong>
                <span>supports</span>
                <strong>{evidence.supported_requirement}</strong>
              </div>
              <p>{evidence.support_path.join(' → ')}</p>
              <small>
                {evidence.source} · {Math.round(evidence.path_confidence * 100)}%
                path confidence · {Math.round(evidence.effective_credit_factor * 100)}%
                credit
              </small>
            </article>
          ))}
        </div>
      ) : (
        <div className="match-semantic-list">
          {match.semantic_skill_score.evidence.map((evidence, index) => (
            <article key={`${evidence.requirement}-${index}`}>
              <header>
                <strong>{evidence.requirement}</strong>
                <span>{Math.round(evidence.cosine_similarity * 100)}%</span>
              </header>
              <small>
                {evidence.resume_section.replaceAll('_', ' ')} · threshold{' '}
                {Math.round(evidence.threshold * 100)}%
              </small>
              <p>{evidence.resume_text_excerpt}</p>
            </article>
          ))}
        </div>
      )}
    </details>
  )
}

function resumeName(resumes: Resume[], id: string) {
  return resumes.find((item) => item.id === id)?.alias || 'Resume'
}

function internshipName(internships: Internship[], id: string) {
  return internships.find((item) => item.id === id)?.label || 'Internship'
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date(value))
}

function errorMessage(error: unknown) {
  return error instanceof ApiError
    ? error.message
    : 'The matching request could not be completed.'
}
