import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../lib/api'
import {
  createCareerRecommendation,
  getCachedCareerRecommendation,
  getCachedGraphCareerRecommendations,
  getGraphCareerRecommendations,
} from '../lib/career'
import {
  getCachedProfileFacts,
  getProfileFacts,
  refreshProfileFacts,
} from '../lib/profile'
import type {
  CareerPathRecommendation,
  CareerRecommendation,
  GraphCareerRecommendations,
} from '../types/career'
import type { UserProfileFacts } from '../types/profile'
import './Career.css'

export function CareerPage() {
  const [facts, setFacts] = useState<UserProfileFacts | null>(
    () => getCachedProfileFacts(),
  )
  const [graph, setGraph] = useState<GraphCareerRecommendations | null>(
    () => getCachedGraphCareerRecommendations(),
  )
  const [recommendation, setRecommendation] =
    useState<CareerRecommendation | null>(() => getCachedCareerRecommendation())
  const [targetField, setTargetField] = useState('')
  const [roles, setRoles] = useState('')
  const [loadingInitial, setLoadingInitial] = useState(true)
  const [refreshingFacts, setRefreshingFacts] = useState(false)
  const [loadingGraph, setLoadingGraph] = useState(false)
  const [creatingRecommendation, setCreatingRecommendation] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    Promise.allSettled([getProfileFacts(), getGraphCareerRecommendations()])
      .then(([factsResult, graphResult]) => {
        if (!active) return
        if (factsResult.status === 'fulfilled') setFacts(factsResult.value)
        if (graphResult.status === 'fulfilled') setGraph(graphResult.value)
      })
      .finally(() => {
        if (active) setLoadingInitial(false)
      })

    return () => {
      active = false
    }
  }, [])

  async function refreshFactsAndGraph() {
    try {
      setRefreshingFacts(true)
      setError('')
      const refreshed = await refreshProfileFacts()
      setFacts(refreshed)
      setLoadingGraph(true)
      setGraph(await getGraphCareerRecommendations())
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setRefreshingFacts(false)
      setLoadingGraph(false)
    }
  }

  async function refreshGraphOnly() {
    try {
      setLoadingGraph(true)
      setError('')
      setGraph(await getGraphCareerRecommendations())
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setLoadingGraph(false)
    }
  }

  async function submitRecommendation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try {
      setCreatingRecommendation(true)
      setError('')
      setRecommendation(
        await createCareerRecommendation({
          target_field: targetField,
          preferred_roles: parseRoles(roles),
        }),
      )
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setCreatingRecommendation(false)
    }
  }

  const topSkills = useMemo(
    () =>
      [...(facts?.skill_inventory ?? [])]
        .sort((left, right) => right.source_count - left.source_count)
        .slice(0, 18),
    [facts],
  )
  const projects = facts?.project_sources.slice(0, 4) ?? []
  const certifications = facts?.certification_sources.slice(0, 4) ?? []
  const graphRecommendations = graph?.recommendations ?? []

  return (
    <main className="app-page career-page">
      <header className="app-page-header career-hero">
        <div>
          <span className="app-page-eyebrow">Career direction</span>
          <h1>Map your profile to realistic paths.</h1>
          <p>
            Career guidance starts from saved resume facts, checks graph role
            fit, then uses AI to turn strengths and gaps into next steps.
          </p>
        </div>
        <button
          className="app-primary-action"
          disabled={refreshingFacts}
          onClick={() => void refreshFactsAndGraph()}
          type="button"
        >
          {refreshingFacts ? 'Refreshing facts...' : 'Refresh profile facts'}
        </button>
      </header>

      {error && <p className="career-error">{error}</p>}

      <section className="career-profile-summary">
        <Metric label="Skills" value={facts?.skill_inventory.length ?? '—'} />
        <Metric label="Skill evidence" value={facts?.skill_sources.length ?? '—'} />
        <Metric label="Projects" value={facts?.project_sources.length ?? '—'} />
        <Metric label="Certifications" value={facts?.certification_sources.length ?? '—'} />
      </section>

      <section className="career-evidence-grid">
        <article className="career-skill-inventory">
          <header>
            <span className="app-page-eyebrow">Profile facts</span>
            <h2>Skill inventory from resumes</h2>
          </header>
          {topSkills.length ? (
            <div>
              {topSkills.map((skill) => (
                <span className={`is-${skill.strength}`} key={skill.canonical_name}>
                  {skill.display_name}
                  <small>{skill.source_count}</small>
                </span>
              ))}
            </div>
          ) : (
            <p>
              No profile facts yet. Upload and parse a resume, then refresh
              profile facts.
            </p>
          )}
        </article>

        <article>
          <header>
            <span className="app-page-eyebrow">Projects</span>
            <h2>Evidence sources</h2>
          </header>
          {projects.length ? (
            projects.map((project) => (
              <div className="career-source-row" key={project.id}>
                <strong>{project.project_name || 'Unnamed project'}</strong>
                <span>{project.skills.slice(0, 4).join(', ') || 'No skills listed'}</span>
              </div>
            ))
          ) : (
            <p>No project facts found yet.</p>
          )}
        </article>

        <article>
          <header>
            <span className="app-page-eyebrow">Credentials</span>
            <h2>Certifications</h2>
          </header>
          {certifications.length ? (
            certifications.map((certification) => (
              <div className="career-source-row" key={certification.id}>
                <strong>{certification.certification_name}</strong>
                <span>{certification.issuer || 'Issuer not extracted'}</span>
              </div>
            ))
          ) : (
            <p>No certifications extracted yet.</p>
          )}
        </article>
      </section>

      <section className="career-graph-section">
        <header>
          <div>
            <span className="app-page-eyebrow">Graph recommendations</span>
            <h2>Role fit from the skill graph</h2>
            <p>
              This layer uses profile skills against graph role data. It is fast
              and does not require an AI call.
            </p>
          </div>
          <button
            className="app-secondary-action"
            disabled={loadingGraph}
            onClick={() => void refreshGraphOnly()}
            type="button"
          >
            {loadingGraph ? 'Refreshing graph...' : 'Refresh graph fit'}
          </button>
        </header>

        {loadingInitial && !graph ? (
          <p className="career-muted-panel">Loading career graph recommendations...</p>
        ) : graphRecommendations.length ? (
          <div className="career-graph-grid">
            {graphRecommendations.slice(0, 6).map((item, index) => (
              <article key={item.role}>
                <span>0{index + 1} · {item.domain}</span>
                <strong>{Math.round(item.fit_score)}%</strong>
                <h3>{item.role}</h3>
                <p>{item.description}</p>
                <div className="career-fit-bar">
                  <i style={{ width: `${Math.min(100, Math.max(4, item.fit_score))}%` }} />
                </div>
                <small>
                  {item.matched_skills.length} matched ·{' '}
                  {item.missing_required_skills.length} required gaps
                </small>
              </article>
            ))}
          </div>
        ) : (
          <p className="career-muted-panel">
            No graph recommendations returned yet. Refresh profile facts after a
            ready resume.
          </p>
        )}

        {graph?.warnings.length ? (
          <div className="career-warning-list">
            {graph.warnings.map((warning) => <p key={warning}>{warning}</p>)}
          </div>
        ) : null}
      </section>

      <section className="career-ai-panel">
        <form onSubmit={submitRecommendation}>
          <span className="app-page-eyebrow">AI recommendation</span>
          <h2>Generate a deeper career plan</h2>
          <p>
            Uses profile facts plus retrieved career guidance to recommend
            paths, gaps, projects, and roadmap steps.
          </p>
          <label>
            Target field
            <input
              onChange={(event) => setTargetField(event.target.value)}
              placeholder="Cybersecurity, AI/ML, Software Engineering..."
              value={targetField}
            />
          </label>
          <label>
            Preferred roles
            <input
              onChange={(event) => setRoles(event.target.value)}
              placeholder="SOC analyst, ML intern, backend intern"
              value={roles}
            />
          </label>
          <button
            className="app-primary-action"
            disabled={creatingRecommendation || !facts?.skill_inventory.length}
            type="submit"
          >
            {creatingRecommendation ? 'Generating recommendation...' : 'Generate career recommendation'}
          </button>
        </form>

        {recommendation ? (
          <CareerRecommendationView recommendation={recommendation} />
        ) : (
          <article className="career-ai-empty">
            <span className="app-page-eyebrow">No AI plan yet</span>
            <h2>Graph fit is useful; AI adds the story.</h2>
            <p>
              Generate a recommendation when you want a student-facing career
              explanation with projects, gaps, and roadmap steps.
            </p>
          </article>
        )}
      </section>
    </main>
  )
}

function CareerRecommendationView({
  recommendation,
}: {
  recommendation: CareerRecommendation
}) {
  const payload = recommendation.recommendation

  return (
    <article className="career-ai-result">
      <header>
        <span className="app-page-eyebrow">
          {recommendation.provider} / {recommendation.model_name}
        </span>
        <h2>{payload.headline}</h2>
        <p>{payload.summary}</p>
        <nav className="career-next-actions" aria-label="Career next steps">
          <Link className="app-secondary-action" to="/matches">
            Compare with a role
          </Link>
          <Link className="app-primary-action" to="/interviews">
            Prepare interview answers
          </Link>
        </nav>
      </header>

      <div className="career-path-columns">
        <PathList paths={payload.primary_paths} title="Primary paths" />
        <PathList paths={payload.secondary_paths} title="Secondary paths" />
      </div>

      <section className="career-roadmap">
        <span className="app-page-eyebrow">Learning roadmap</span>
        {payload.learning_roadmap.slice(0, 5).map((step) => (
          <article key={step.order}>
            <span>{String(step.order).padStart(2, '0')}</span>
            <div>
              <strong>{step.title}</strong>
              <p>{step.focus}</p>
              <small>{step.expected_outcome}</small>
            </div>
          </article>
        ))}
      </section>

      <section className="career-projects">
        <span className="app-page-eyebrow">Recommended projects</span>
        <div>
          {payload.recommended_projects.slice(0, 3).map((project) => (
            <article key={project.title}>
              <strong>{project.title}</strong>
              <p>{project.goal}</p>
              <small>{project.tools.slice(0, 5).join(', ')}</small>
            </article>
          ))}
        </div>
      </section>
    </article>
  )
}

function PathList({
  paths,
  title,
}: {
  paths: CareerPathRecommendation[]
  title: string
}) {
  return (
    <section>
      <h3>{title}</h3>
      {paths.length ? (
        paths.slice(0, 3).map((path) => (
          <article key={path.path}>
            <span>{path.fit_level.replaceAll('_', ' ')}</span>
            <strong>{path.path}</strong>
            <p>{path.why_it_fits}</p>
            <small>{path.missing_skills.slice(0, 4).join(', ') || 'No major gaps returned'}</small>
          </article>
        ))
      ) : (
        <p>No paths returned.</p>
      )}
    </section>
  )
}

function Metric({ label, value }: { label: string; value: number | string }) {
  return (
    <article>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  )
}

function parseRoles(value: string) {
  return value
    .split(',')
    .map((role) => role.trim())
    .filter(Boolean)
    .slice(0, 8)
}

function errorMessage(error: unknown) {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Career request failed.'
}
