import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../lib/api'
import {
  createGitHubAnalysis,
  createGitHubSnapshot,
  getCachedGitHubAnalysis,
  getCachedGitHubCompactSnapshot,
  getLatestGitHubAnalysis,
  getLatestGitHubCompactSnapshot,
} from '../lib/github'
import type {
  GitHubCompactRepository,
  GitHubCompactSnapshotResponse,
  GitHubProfileAnalysis,
} from '../types/github'
import './GitHub.css'

export function GitHubPage() {
  const [snapshot, setSnapshot] = useState<GitHubCompactSnapshotResponse | null>(
    () => getCachedGitHubCompactSnapshot(),
  )
  const [analysis, setAnalysis] = useState<GitHubProfileAnalysis | null>(
    () => getCachedGitHubAnalysis(),
  )
  const [username, setUsername] = useState('')
  const [targetField, setTargetField] = useState('')
  const [roles, setRoles] = useState('')
  const [loadingInitial, setLoadingInitial] = useState(true)
  const [creatingSnapshot, setCreatingSnapshot] = useState(false)
  const [creatingAnalysis, setCreatingAnalysis] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    Promise.allSettled([
      getLatestGitHubCompactSnapshot(),
      getLatestGitHubAnalysis(),
    ])
      .then(([snapshotResult, analysisResult]) => {
        if (!active) return
        if (snapshotResult.status === 'fulfilled') {
          setSnapshot(snapshotResult.value)
          setUsername(snapshotResult.value.github_username)
        }
        if (analysisResult.status === 'fulfilled') {
          setAnalysis(analysisResult.value)
          setTargetField(
            typeof analysisResult.value.analysis_request.target_field === 'string'
              ? analysisResult.value.analysis_request.target_field
              : '',
          )
        }
      })
      .finally(() => {
        if (active) setLoadingInitial(false)
      })

    return () => {
      active = false
    }
  }, [])

  async function submitSnapshot(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try {
      setCreatingSnapshot(true)
      setError('')
      const created = await createGitHubSnapshot({
        github_username: username,
        repository_limit: 12,
      })
      setSnapshot({
        id: created.id,
        github_username: created.github_username,
        compact_snapshot: created.compact_snapshot,
        repository_limit: created.repository_limit,
        fetched_at: created.fetched_at,
        created_at: created.created_at,
      })
      setAnalysis(null)
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setCreatingSnapshot(false)
    }
  }

  async function submitAnalysis(forceRefresh = false) {
    try {
      setCreatingAnalysis(true)
      setError('')
      setAnalysis(
        await createGitHubAnalysis({
          snapshot_id: snapshot?.id ?? null,
          target_field: targetField,
          preferred_roles: parseRoles(roles),
          force_refresh: forceRefresh,
        }),
      )
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setCreatingAnalysis(false)
    }
  }

  const compact = snapshot?.compact_snapshot
  const profile = compact?.profile
  const summary = compact?.summary
  const repositories = useMemo(
    () => [...(compact?.repositories ?? [])].sort(sortReposForDisplay).slice(0, 6),
    [compact?.repositories],
  )
  const topLanguages = summary?.top_languages ?? []

  return (
    <main className="app-page github-page">
      <header className="app-page-header github-hero">
        <div>
          <span className="app-page-eyebrow">GitHub portfolio</span>
          <h1>Turn repositories into career evidence.</h1>
          <p>
            Fetch a compact GitHub snapshot, review the profile signals, then
            generate an AI portfolio analysis for resume and career readiness.
          </p>
        </div>
        {snapshot && (
          <a
            className="github-profile-link"
            href={profile?.html_url ?? `https://github.com/${snapshot.github_username}`}
            rel="noreferrer"
            target="_blank"
          >
            Open GitHub profile
          </a>
        )}
      </header>

      {error && <p className="github-error">{error}</p>}

      <section className="github-control-panel">
        <form onSubmit={submitSnapshot}>
          <span className="app-page-eyebrow">Profile scan</span>
          <label>
            GitHub username
            <input
              onChange={(event) => setUsername(event.target.value)}
              placeholder="octocat"
              required
              value={username}
            />
          </label>
          <button className="app-primary-action" disabled={creatingSnapshot} type="submit">
            {creatingSnapshot ? 'Creating snapshot...' : 'Create fresh snapshot'}
          </button>
        </form>

        <form
          onSubmit={(event) => {
            event.preventDefault()
            void submitAnalysis(false)
          }}
        >
          <span className="app-page-eyebrow">AI portfolio analysis</span>
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
              placeholder="SOC analyst, backend intern"
              value={roles}
            />
          </label>
          <div>
            <button
              className="app-primary-action"
              disabled={!snapshot || creatingAnalysis}
              type="submit"
            >
              {creatingAnalysis ? 'Generating analysis...' : 'Generate analysis'}
            </button>
            <button
              className="app-secondary-action"
              disabled={!snapshot || creatingAnalysis}
              onClick={() => void submitAnalysis(true)}
              type="button"
            >
              Force refresh
            </button>
          </div>
        </form>
      </section>

      {loadingInitial && !snapshot ? (
        <section className="github-empty-state">
          <span className="app-page-eyebrow">Loading</span>
          <h2>Checking for saved GitHub data...</h2>
        </section>
      ) : snapshot ? (
        <>
          <section className="github-profile-summary">
            <article>
              <span className="app-page-eyebrow">Snapshot</span>
              <h2>{profile?.name || snapshot.github_username}</h2>
              <p>{profile?.bio || 'No GitHub bio found in the compact snapshot.'}</p>
              <small>
                @{snapshot.github_username} · fetched {formatDate(snapshot.fetched_at)}
              </small>
            </article>
            <Metric label="Public repos" value={profile?.public_repos ?? '—'} />
            <Metric label="Analyzed" value={summary?.analyzed_repository_count ?? '—'} />
            <Metric label="READMEs" value={summary?.repositories_with_readme_count ?? '—'} />
            <Metric label="Stars" value={summary?.total_stars ?? '—'} />
          </section>

          <section className="github-language-section">
            <header>
              <span className="app-page-eyebrow">Technology signal</span>
              <h2>Top languages and portfolio shape</h2>
            </header>
            <div className="github-language-bars">
              {topLanguages.length ? (
                topLanguages.map((language) => (
                  <LanguageBar
                    key={language}
                    language={language}
                    totals={compact?.language_totals ?? {}}
                  />
                ))
              ) : (
                <p>No language totals were available in this snapshot.</p>
              )}
            </div>
          </section>

          <section className="github-repository-grid">
            <header>
              <span className="app-page-eyebrow">Repository evidence</span>
              <h2>Repositories the system scanned</h2>
            </header>
            <div>
              {repositories.map((repository) => (
                <RepositoryCard key={repository.name} repository={repository} />
              ))}
            </div>
          </section>
        </>
      ) : (
        <section className="github-empty-state">
          <span className="app-page-eyebrow">No snapshot yet</span>
          <h2>Create a GitHub snapshot to begin.</h2>
          <p>
            This uses the public GitHub API and stores both the raw scan and the
            compact snapshot in the backend.
          </p>
        </section>
      )}

      {analysis && <GitHubAnalysisView analysis={analysis} />}
    </main>
  )
}

function GitHubAnalysisView({ analysis }: { analysis: GitHubProfileAnalysis }) {
  const payload = analysis.analysis

  return (
    <section className="github-analysis-section">
      <header>
        <div>
          <span className="app-page-eyebrow">AI portfolio review</span>
          <h2>{payload.headline}</h2>
          <p>{payload.summary}</p>
          <nav className="github-next-actions" aria-label="GitHub next steps">
            <Link className="app-secondary-action" to="/career">
              Use for career direction
            </Link>
            <Link className="app-primary-action" to="/interviews">
              Use for interview prep
            </Link>
          </nav>
        </div>
        <strong>{Math.round(payload.portfolio_score)}%</strong>
      </header>

      <div className="github-analysis-columns">
        <AnalysisList
          items={payload.strong_repositories.map((item) => ({
            title: item.repository_name,
            body: item.why_it_matters,
            meta: item.evidence_level,
          }))}
          title="Strong repositories"
        />
        <AnalysisList
          items={payload.resume_worthy_projects.map((item) => ({
            title: item.repository_name,
            body: item.resume_bullet_suggestion,
            meta: item.demonstrated_skills.slice(0, 3).join(', '),
          }))}
          title="Resume-worthy projects"
        />
        <AnalysisList
          items={payload.weak_repositories.map((item) => ({
            title: item.repository_name,
            body: item.suggested_fix,
            meta: `${item.priority} priority`,
          }))}
          title="Needs improvement"
        />
      </div>

      <div className="github-action-grid">
        <section>
          <span className="app-page-eyebrow">Skills detected</span>
          <div>
            {[
              ...payload.technology_summary.top_languages,
              ...payload.technology_summary.detected_frameworks_or_tools,
              ...payload.technology_summary.likely_skill_areas,
            ]
              .filter(Boolean)
              .slice(0, 18)
              .map((skill) => <small key={skill}>{skill}</small>)}
          </div>
        </section>

        <section>
          <span className="app-page-eyebrow">Recommended actions</span>
          {payload.recommended_actions.slice(0, 4).map((action) => (
            <article key={action.title}>
              <strong>{action.title}</strong>
              <p>{action.reason}</p>
            </article>
          ))}
        </section>

        <section>
          <span className="app-page-eyebrow">Career alignment</span>
          {payload.career_alignment.slice(0, 3).map((alignment) => (
            <article key={alignment.role_or_field}>
              <strong>{alignment.role_or_field}</strong>
              <p>{alignment.next_project_idea}</p>
            </article>
          ))}
        </section>
      </div>
    </section>
  )
}

function AnalysisList({
  items,
  title,
}: {
  items: Array<{ title: string; body: string; meta: string }>
  title: string
}) {
  return (
    <section>
      <h3>{title}</h3>
      {items.length ? (
        items.slice(0, 4).map((item) => (
          <article key={`${title}-${item.title}`}>
            <span>{item.meta}</span>
            <strong>{item.title}</strong>
            <p>{item.body}</p>
          </article>
        ))
      ) : (
        <p>No items returned.</p>
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

function RepositoryCard({
  repository,
}: {
  repository: GitHubCompactRepository
}) {
  const preview =
    repository.description ||
    cleanMarkdownPreview(repository.readme_excerpt) ||
    'No description found.'

  return (
    <article>
      <div>
        <span>{repository.primary_language || 'Repository'}</span>
        <small>{repository.has_readme ? 'README' : 'No README'}</small>
      </div>
      <h3>{repository.name}</h3>
      <p>{preview}</p>
      <footer>
        <span>{repository.stars} stars</span>
        <span>{repository.forks} forks</span>
        {repository.html_url && (
          <a href={repository.html_url} rel="noreferrer" target="_blank">
            Open
          </a>
        )}
      </footer>
    </article>
  )
}

function cleanMarkdownPreview(value: string | null) {
  if (!value) return ''

  return value
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/!\[[^\]]*]\([^)]+\)/g, ' ')
    .replace(/\[([^\]]+)]\([^)]+\)/g, '$1')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^>\s?/gm, '')
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/__([^_]+)__/g, '$1')
    .replace(/_([^_]+)_/g, '$1')
    .replace(/<[^>]+>/g, ' ')
    .replace(/[#*_~|]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 220)
}

function LanguageBar({
  language,
  totals,
}: {
  language: string
  totals: Record<string, number>
}) {
  const max = Math.max(...Object.values(totals), 1)
  const value = totals[language] ?? 0
  const width = Math.max(7, Math.round((value / max) * 100))

  return (
    <article>
      <span>{language}</span>
      <i>
        <b style={{ width: `${width}%` }} />
      </i>
      <small>{formatBytes(value)}</small>
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

function sortReposForDisplay(
  left: GitHubCompactRepository,
  right: GitHubCompactRepository,
) {
  const leftScore = Number(left.has_readme) * 10 + left.stars + left.forks
  const rightScore = Number(right.has_readme) * 10 + right.stars + right.forks
  return rightScore - leftScore
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function formatBytes(value: number) {
  if (!value) return '0 bytes'
  if (value < 1024) return `${value} bytes`
  if (value < 1024 * 1024) return `${Math.round(value / 1024)} KB`
  return `${(value / 1024 / 1024).toFixed(1)} MB`
}

function errorMessage(error: unknown) {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'GitHub request failed.'
}
