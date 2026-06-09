import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { getLatestGitHubAnalysis } from '../lib/github'
import {
  getGuidanceReferences,
  getMatchExplanation,
  getMatchLearningPaths,
  loadMatchAnalyses,
} from '../lib/matches'
import type { GitHubProfileAnalysis } from '../types/github'
import type {
  MatchAnalysis,
  MatchExplanation,
  MatchLearningPaths,
} from '../types/match'
import './Interviews.css'

export function InterviewsPage() {
  const [analyses, setAnalyses] = useState<MatchAnalysis[]>([])
  const [selectedAnalysisId, setSelectedAnalysisId] = useState('')
  const [explanation, setExplanation] = useState<MatchExplanation | null>(null)
  const [learningPaths, setLearningPaths] = useState<MatchLearningPaths | null>(null)
  const [githubAnalysis, setGithubAnalysis] =
    useState<GitHubProfileAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingContext, setLoadingContext] = useState(false)

  useEffect(() => {
    let active = true

    Promise.allSettled([loadMatchAnalyses(), getLatestGitHubAnalysis()])
      .then(([analysesResult, githubResult]) => {
        if (!active) return
        if (analysesResult.status === 'fulfilled') {
          setAnalyses(analysesResult.value)
          setSelectedAnalysisId(analysesResult.value[0]?.id ?? '')
        }
        if (githubResult.status === 'fulfilled') {
          setGithubAnalysis(githubResult.value)
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    let active = true

    async function loadSelectedContext() {
      if (!selectedAnalysisId) {
        if (!active) return
        setExplanation(null)
        setLearningPaths(null)
        return
      }

      const references = getGuidanceReferences(selectedAnalysisId)
      if (!active) return
      setLoadingContext(true)
      setExplanation(null)
      setLearningPaths(null)

      const [explanationResult, pathsResult] = await Promise.allSettled([
        references
          ? getMatchExplanation(references.explanationId)
          : Promise.resolve(null),
        getMatchLearningPaths(selectedAnalysisId),
      ])

      if (!active) return
      if (
        explanationResult.status === 'fulfilled' &&
        explanationResult.value
      ) {
        setExplanation(explanationResult.value)
      }
      if (pathsResult.status === 'fulfilled') {
        setLearningPaths(pathsResult.value)
      }
      setLoadingContext(false)
    }

    void loadSelectedContext().catch(() => {
      if (active) {
        if (
          selectedAnalysisId
        ) {
          setLoadingContext(false)
        }
      }
    })

    return () => {
      active = false
    }
  }, [selectedAnalysisId])

  const selectedAnalysis = analyses.find(
    (analysis) => analysis.id === selectedAnalysisId,
  )
  const readiness = useMemo(
    () =>
      buildReadiness({
        explanation,
        githubAnalysis,
        learningPaths,
        selectedAnalysis,
      }),
    [explanation, githubAnalysis, learningPaths, selectedAnalysis],
  )

  return (
    <main className="app-page interviews-page">
      <header className="app-page-header interviews-hero">
        <div>
          <span className="app-page-eyebrow">Interview preparation</span>
          <h1>Practice from the evidence you already saved.</h1>
          <p>
            Choose a saved match and prepare for the role with questions,
            talking points, gap-focused practice, and portfolio evidence.
          </p>
        </div>
      </header>

      <section className="interview-control-panel">
        <label>
          Saved match analysis
          <select
            disabled={loading || analyses.length === 0}
            onChange={(event) => setSelectedAnalysisId(event.target.value)}
            value={selectedAnalysisId}
          >
            {analyses.length ? (
              analyses.map((analysis) => (
                <option key={analysis.id} value={analysis.id}>
                  {Math.round(analysis.overall_score)}% match ·{' '}
                  {formatDate(analysis.created_at)}
                </option>
              ))
            ) : (
              <option value="">No saved analyses yet</option>
            )}
          </select>
        </label>
        <div>
          <span className="app-page-eyebrow">Selected score</span>
          <strong>
            {selectedAnalysis ? `${Math.round(selectedAnalysis.overall_score)}%` : '—'}
          </strong>
        </div>
      </section>

      {!loading && analyses.length === 0 && (
        <section className="interview-empty-state">
          <span className="app-page-eyebrow">No match selected</span>
          <h2>Save a match analysis before interview prep.</h2>
          <p>
            Interview practice works best when it can use a resume, target
            internship, match score, gaps, and guidance.
          </p>
          <Link className="app-primary-action" to="/matches">
            Create match analysis
          </Link>
        </section>
      )}

      <section className="interview-readiness-grid">
        {readiness.map((item) => (
          <article className={item.available ? 'is-ready' : ''} key={item.label}>
            <span>{item.available ? 'Ready' : 'Missing'}</span>
            <h2>{item.label}</h2>
            <p>{item.description}</p>
          </article>
        ))}
      </section>

      <section className="interview-mode-grid">
        <InterviewModeCard
          available={Boolean(selectedAnalysis)}
          description="Prepare with a structured set of likely questions, answer hints, and evidence from your own resume."
          disabledReason="Question generation is coming soon."
          steps={[
            'Role-specific technical questions',
            'Resume and project questions',
            'Suggested answer angles',
          ]}
          title="Question Bank Mode"
        />
        <InterviewModeCard
          available={Boolean(selectedAnalysis)}
          description="Practice like a real interview: one question at a time, answer in text, then review final feedback."
          disabledReason="Live interview sessions are coming soon."
          steps={[
            'One question at a time',
            'Follow-up questions from your answer',
            'Final feedback after the full session',
          ]}
          title="Live Interview Mode"
        />
      </section>

      <section className="interview-context-layout">
        <article>
          <span className="app-page-eyebrow">Preparation board</span>
          <h2>{loadingContext ? 'Loading context...' : 'What to prepare from'}</h2>
          <ContextList
            explanation={explanation}
            githubAnalysis={githubAnalysis}
            learningPaths={learningPaths}
            selectedAnalysis={selectedAnalysis}
          />
        </article>

        <article>
          <span className="app-page-eyebrow">Practice plan</span>
          <h2>How this helps you answer better</h2>
          <div className="interview-practice-list">
            <section>
              <strong>Explain your strengths</strong>
              <p>Turn matched skills into confident answers with evidence.</p>
            </section>
            <section>
              <strong>Defend weak areas</strong>
              <p>Prepare honest answers for missing or partial requirements.</p>
            </section>
            <section>
              <strong>Use projects well</strong>
              <p>Connect resume and GitHub work to internship requirements.</p>
            </section>
            <section>
              <strong>Leave with next steps</strong>
              <p>Use the final review to focus on gaps most likely to appear.</p>
            </section>
          </div>
        </article>
      </section>
    </main>
  )
}

function InterviewModeCard({
  available,
  description,
  disabledReason,
  steps,
  title,
}: {
  available: boolean
  description: string
  disabledReason: string
  steps: string[]
  title: string
}) {
  return (
    <article>
      <span className="app-page-eyebrow">Practice mode</span>
      <h2>{title}</h2>
      <p>{description}</p>
      <ul>
        {steps.map((step) => <li key={step}>{step}</li>)}
      </ul>
      <button className="app-primary-action" disabled={!available} type="button">
        Coming soon
      </button>
      <small>{available ? disabledReason : 'Needs saved match context.'}</small>
    </article>
  )
}

function ContextList({
  explanation,
  githubAnalysis,
  learningPaths,
  selectedAnalysis,
}: {
  explanation: MatchExplanation | null
  githubAnalysis: GitHubProfileAnalysis | null
  learningPaths: MatchLearningPaths | null
  selectedAnalysis: MatchAnalysis | undefined
}) {
  const gaps = explanation?.explanation.gaps.slice(0, 4) ?? []
  const talkingPoints =
    explanation?.explanation.interview_talking_points.slice(0, 4) ?? []
  const pathTargets =
    learningPaths?.learning_paths.map((path) => path.target_skill).slice(0, 5) ?? []

  return (
    <div className="interview-context-list">
      <section>
        <strong>Match summary</strong>
        <p>
          {selectedAnalysis
            ? `${Math.round(selectedAnalysis.overall_score)}% saved match selected for interview preparation.`
            : 'No match selected.'}
        </p>
      </section>
      <section>
        <strong>AI explanation</strong>
        <p>
          {explanation
            ? explanation.explanation.score_card.headline
            : 'Generate AI guidance from the match page to unlock richer talking points.'}
        </p>
      </section>
      <section>
        <strong>Likely interview prompts</strong>
        <ul>
          {talkingPoints.length ? (
            talkingPoints.map((point) => (
              <li key={`${point.requirement}-${point.prompt}`}>
                {point.requirement}: {point.prompt}
              </li>
            ))
          ) : (
            <li>Generate match guidance first to populate role-specific prompts.</li>
          )}
        </ul>
      </section>
      <section>
        <strong>Gap focus</strong>
        <p>
          {gaps.length
            ? gaps.map((gap) => gap.requirement).join(', ')
            : 'No AI gap list available yet. The interview can still use the base match.'}
        </p>
      </section>
      <section>
        <strong>Learning path targets</strong>
        <p>{pathTargets.length ? pathTargets.join(', ') : 'No learning path targets returned yet.'}</p>
      </section>
      <section>
        <strong>GitHub portfolio</strong>
        <p>
          {githubAnalysis
            ? `${githubAnalysis.github_username}: ${githubAnalysis.analysis.headline}`
            : 'Analyze GitHub to add portfolio evidence to interview prep.'}
        </p>
      </section>
    </div>
  )
}

function buildReadiness({
  explanation,
  githubAnalysis,
  learningPaths,
  selectedAnalysis,
}: {
  explanation: MatchExplanation | null
  githubAnalysis: GitHubProfileAnalysis | null
  learningPaths: MatchLearningPaths | null
  selectedAnalysis: MatchAnalysis | undefined
}) {
  return [
    {
      available: Boolean(selectedAnalysis),
      description: 'Core match score and requirement evidence.',
      label: 'Saved match',
    },
    {
      available: Boolean(explanation),
      description: 'Strengths, gaps, resume actions, and talking points.',
      label: 'AI explanation',
    },
    {
      available: Boolean(learningPaths?.learning_paths.length),
      description: 'Graph-backed gaps and learning targets.',
      label: 'Learning paths',
    },
    {
      available: Boolean(githubAnalysis),
      description: 'Optional project evidence from GitHub.',
      label: 'GitHub context',
    },
  ]
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}
