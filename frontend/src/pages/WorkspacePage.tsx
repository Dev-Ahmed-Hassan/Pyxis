import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { loadInternships } from '../lib/internships'
import { loadMatchAnalyses } from '../lib/matches'
import { loadResumes } from '../lib/resumes'
import type { Internship } from '../types/internship'
import type { MatchAnalysis } from '../types/match'
import type { Resume } from '../types/resume'
import './Workspace.css'

const modules = [
  {
    number: '01',
    title: 'Resume evidence',
    description: 'Upload resumes, inspect parsed profile data, and confirm what the system extracted.',
    to: '/resumes',
    status: 'Live',
  },
  {
    number: '02',
    title: 'Internship requirements',
    description: 'Save target roles and review the required skills, domains, and soft-skill signals.',
    to: '/internships',
    status: 'Live',
  },
  {
    number: '03',
    title: 'Match intelligence',
    description: 'Compare resume evidence with internship requirements, then generate AI guidance.',
    to: '/matches',
    status: 'Live',
  },
  {
    number: '04',
    title: 'Career direction',
    description: 'Use profile facts and graph recommendations to plan realistic next career paths.',
    to: '/career',
    status: 'Live',
  },
  {
    number: '05',
    title: 'GitHub portfolio',
    description: 'Analyze public GitHub work, identify resume-worthy repos, and improve project presentation.',
    to: '/github',
    status: 'Live',
  },
  {
    number: '06',
    title: 'Interview preparation',
    description: 'Turn a selected match into question banks, live interview practice, and feedback.',
    to: '/interviews',
    status: 'Shell',
  },
]

export function WorkspacePage() {
  const [resumes, setResumes] = useState<Resume[]>([])
  const [internships, setInternships] = useState<Internship[]>([])
  const [analyses, setAnalyses] = useState<MatchAnalysis[]>([])
  const [loading, setLoading] = useState(true)
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
      .catch(() => {
        if (active) setError('Workspace data could not be refreshed.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  const readyResumes = resumes.filter((resume) => resume.processing_status === 'ready')
  const readyInternships = internships.filter(
    (internship) => internship.processing_status === 'ready',
  )
  const failedItems =
    resumes.filter((resume) => resume.processing_status === 'failed').length +
    internships.filter((internship) => internship.processing_status === 'failed').length

  const latestAnalysis = analyses[0] ?? null
  const bestAnalysis = useMemo(
    () =>
      analyses.reduce<MatchAnalysis | null>(
        (best, analysis) =>
          !best || analysis.overall_score > best.overall_score ? analysis : best,
        null,
      ),
    [analyses],
  )

  const nextAction = getNextAction({
    analyses,
    readyInternships: readyInternships.length,
    readyResumes: readyResumes.length,
  })

  return (
    <main className="app-page workspace-overview">
      <header className="app-page-header workspace-hero">
        <div>
          <span className="app-page-eyebrow">Workspace overview</span>
          <h1>Your career evidence command center.</h1>
          <p>
            Start with resumes and internships, then move into matching, AI
            explanations, GitHub portfolio review, career direction, and
            interview preparation.
          </p>
        </div>
        <Link className="workspace-start-link" to={nextAction.to}>
          {nextAction.action}
        </Link>
      </header>

      {error && <p className="workspace-error">{error}</p>}

      <section className="workspace-metrics" aria-label="Workspace summary">
        <Metric label="Ready resumes" value={readyResumes.length} note={`${resumes.length} total`} />
        <Metric
          label="Ready internships"
          value={readyInternships.length}
          note={`${internships.length} total`}
        />
        <Metric label="Saved matches" value={analyses.length} note="analysis history" />
        <Metric
          label="Best score"
          value={bestAnalysis ? `${Math.round(bestAnalysis.overall_score)}%` : '—'}
          note={bestAnalysis ? 'highest saved match' : 'save a match first'}
        />
      </section>

      <section className="workspace-focus-grid">
        <article className="workspace-next-card">
          <span className="app-page-eyebrow">Next best step</span>
          <h2>{nextAction.title}</h2>
          <p>{nextAction.description}</p>
          <Link className="app-primary-action" to={nextAction.to}>
            {nextAction.action}
          </Link>
        </article>

        <article className="workspace-latest-card">
          <span className="app-page-eyebrow">Latest saved match</span>
          {latestAnalysis ? (
            <>
              <strong>{Math.round(latestAnalysis.overall_score)}%</strong>
              <h2>{matchLabel(resumes, internships, latestAnalysis)}</h2>
              <p>
                Created {formatDate(latestAnalysis.created_at)}
                {latestAnalysis.stale_at ? ' · stale' : ''}
              </p>
              <Link to="/matches">Open match analysis</Link>
            </>
          ) : (
            <>
              <strong>—</strong>
              <h2>No saved analysis yet</h2>
              <p>Run a match preview and save it to unlock the guidance layer.</p>
              <Link to="/matches">Go to matching</Link>
            </>
          )}
        </article>

        <article className="workspace-health-card">
          <span className="app-page-eyebrow">Pipeline health</span>
          <h2>{loading ? 'Refreshing workspace...' : failedItems ? 'Needs attention' : 'Systems ready'}</h2>
          <p>
            {failedItems
              ? `${failedItems} resume or internship item failed processing. Retry it from its module.`
              : 'Parsed data is ready to power matching, explanations, recommendations, and dashboards.'}
          </p>
        </article>
      </section>

      <section className="workspace-module-grid">
        {modules.map((module) => (
          <Link className="workspace-module" key={module.number} to={module.to}>
            <div>
              <span>{module.number}</span>
              <small>{module.status}</small>
            </div>
            <h2>{module.title}</h2>
            <p>{module.description}</p>
            <strong>Open module</strong>
          </Link>
        ))}
      </section>

      <section className="workspace-flow">
        <div>
          <span className="app-page-eyebrow">Core application flow</span>
          <h2>One profile, several connected decisions.</h2>
        </div>
        <ol>
          <li><span>01</span>Collect resume and profile evidence</li>
          <li><span>02</span>Parse internship requirements</li>
          <li><span>03</span>Explain the match and its gaps</li>
          <li><span>04</span>Turn gaps into projects and preparation</li>
          <li><span>05</span>Use GitHub and career data as extra evidence</li>
        </ol>
      </section>
    </main>
  )
}

function Metric({
  label,
  note,
  value,
}: {
  label: string
  note: string
  value: number | string
}) {
  return (
    <article>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </article>
  )
}

function getNextAction({
  analyses,
  readyInternships,
  readyResumes,
}: {
  analyses: MatchAnalysis[]
  readyInternships: number
  readyResumes: number
}) {
  if (!readyResumes) {
    return {
      action: 'Upload resume',
      description: 'The matcher needs at least one ready parsed resume before it can compare evidence.',
      title: 'Add your first resume',
      to: '/resumes',
    }
  }
  if (!readyInternships) {
    return {
      action: 'Add internship',
      description: 'Add a target internship so PYXIS can extract requirements and prepare a comparison.',
      title: 'Create a target role',
      to: '/internships',
    }
  }
  if (!analyses.length) {
    return {
      action: 'Run matching',
      description: 'You have enough parsed data. Generate the first match analysis and inspect the gaps.',
      title: 'Compare resume with internship',
      to: '/matches',
    }
  }
  return {
    action: 'Review analyses',
    description: 'Open saved comparisons, generate guidance, and use gaps to plan projects or interview prep.',
    title: 'Continue from saved evidence',
    to: '/matches',
  }
}

function matchLabel(
  resumes: Resume[],
  internships: Internship[],
  analysis: MatchAnalysis,
) {
  const resume = resumes.find((item) => item.id === analysis.resume_id)
  const internship = internships.find(
    (item) => item.id === analysis.internship_input_id,
  )
  return `${resume?.alias ?? 'Resume'} → ${internship?.label ?? 'Internship'}`
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}
