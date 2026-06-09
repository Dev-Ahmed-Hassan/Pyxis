import { useEffect, useMemo, useState } from 'react'
import {
  ArrowRight,
  BookOpen,
  Check,
  Flag,
  MessageSquare,
  RefreshCw,
  Send,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { ApiError } from '../lib/api'
import { getLatestGitHubAnalysis } from '../lib/github'
import {
  completeInterviewSession,
  createInterviewPreparation,
  createInterviewSession,
  getNextInterviewQuestion,
  submitInterviewAnswer,
} from '../lib/interviews'
import {
  getGuidanceReferences,
  getMatchExplanation,
  getMatchLearningPaths,
  loadMatchAnalyses,
} from '../lib/matches'
import type { GitHubProfileAnalysis } from '../types/github'
import type {
  InterviewDifficulty,
  InterviewEvaluation,
  InterviewFocusArea,
  InterviewPreparation,
  InterviewQuestion,
  InterviewSession,
} from '../types/interview'
import type {
  MatchAnalysis,
  MatchExplanation,
  MatchLearningPaths,
} from '../types/match'
import './Interviews.css'

type InterviewMode = 'overview' | 'preparation' | 'live'

const focusOptions: Array<{
  value: InterviewFocusArea
  label: string
}> = [
  { value: 'technical', label: 'Technical' },
  { value: 'resume', label: 'Resume' },
  { value: 'behavioral', label: 'Behavioral' },
  { value: 'situational', label: 'Situational' },
]

export function InterviewsPage() {
  const [analyses, setAnalyses] = useState<MatchAnalysis[]>([])
  const [selectedAnalysisId, setSelectedAnalysisId] = useState('')
  const [explanation, setExplanation] = useState<MatchExplanation | null>(null)
  const [learningPaths, setLearningPaths] = useState<MatchLearningPaths | null>(
    null,
  )
  const [githubAnalysis, setGithubAnalysis] =
    useState<GitHubProfileAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingContext, setLoadingContext] = useState(false)
  const [mode, setMode] = useState<InterviewMode>('overview')
  const [difficulty, setDifficulty] =
    useState<InterviewDifficulty>('intermediate')
  const [questionCount, setQuestionCount] = useState(8)
  const [focusAreas, setFocusAreas] = useState<InterviewFocusArea[]>([
    'technical',
    'resume',
    'behavioral',
  ])
  const [preparation, setPreparation] =
    useState<InterviewPreparation | null>(null)
  const [session, setSession] = useState<InterviewSession | null>(null)
  const [question, setQuestion] = useState<InterviewQuestion | null>(null)
  const [questionsRemaining, setQuestionsRemaining] = useState(0)
  const [answer, setAnswer] = useState('')
  const [evaluation, setEvaluation] =
    useState<InterviewEvaluation | null>(null)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')

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
      setMode('overview')
      setPreparation(null)
      setSession(null)
      setQuestion(null)
      setEvaluation(null)
      setError('')
      if (!selectedAnalysisId) {
        setExplanation(null)
        setLearningPaths(null)
        return
      }

      const references = getGuidanceReferences(selectedAnalysisId)
      setLoadingContext(true)
      const [explanationResult, pathsResult] = await Promise.allSettled([
        references
          ? getMatchExplanation(references.explanationId)
          : Promise.resolve(null),
        getMatchLearningPaths(selectedAnalysisId),
      ])

      if (!active) return
      setExplanation(
        explanationResult.status === 'fulfilled'
          ? explanationResult.value
          : null,
      )
      setLearningPaths(
        pathsResult.status === 'fulfilled' ? pathsResult.value : null,
      )
      setLoadingContext(false)
    }

    void loadSelectedContext().catch(() => {
      if (active) setLoadingContext(false)
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

  function requestContext() {
    return {
      matchAnalysisId: selectedAnalysisId,
      matchExplanationId: explanation?.id ?? null,
      difficulty,
      questionCount,
      focusAreas,
    }
  }

  async function generatePreparation(forceRefresh = false) {
    if (!selectedAnalysisId) return
    setWorking(true)
    setError('')
    try {
      setPreparation(
        await createInterviewPreparation(requestContext(), forceRefresh),
      )
      setMode('preparation')
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setWorking(false)
    }
  }

  async function startLiveInterview() {
    if (!selectedAnalysisId) return
    setWorking(true)
    setError('')
    setEvaluation(null)
    setAnswer('')
    try {
      const created = await createInterviewSession(requestContext())
      const next = await getNextInterviewQuestion(created.id)
      setSession(created)
      setQuestion(next.question)
      setQuestionsRemaining(next.questions_remaining)
      setMode('live')
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setWorking(false)
    }
  }

  async function submitAnswer() {
    if (!session || !question || answer.trim().length < 10) return
    setWorking(true)
    setError('')
    try {
      const acknowledgement = await submitInterviewAnswer(
        session.id,
        question.id,
        answer.trim(),
      )
      setAnswer('')
      if (acknowledgement.session_complete) {
        await finishInterview(session.id)
        return
      }
      const next = await getNextInterviewQuestion(session.id)
      setQuestion(next.question)
      setQuestionsRemaining(next.questions_remaining)
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setWorking(false)
    }
  }

  async function finishInterview(sessionId = session?.id) {
    if (!sessionId) return
    setWorking(true)
    setError('')
    try {
      const result = await completeInterviewSession(sessionId)
      setEvaluation(result)
      setQuestion(null)
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setWorking(false)
    }
  }

  function toggleFocus(value: InterviewFocusArea) {
    setFocusAreas((current) =>
      current.includes(value)
        ? current.length > 1
          ? current.filter((item) => item !== value)
          : current
        : [...current, value],
    )
  }

  return (
    <main className="app-page interviews-page">
      <header className="app-page-header interviews-hero">
        <div>
          <span className="app-page-eyebrow">Interview preparation</span>
          <h1>Practice from the evidence you already saved.</h1>
          <p>
            Build a role-specific question bank or conduct a complete interview
            with feedback held until the end.
          </p>
        </div>
      </header>

      <section className="interview-control-panel">
        <label>
          Saved match analysis
          <select
            disabled={loading || analyses.length === 0 || working}
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
            {selectedAnalysis
              ? `${Math.round(selectedAnalysis.overall_score)}%`
              : '—'}
          </strong>
        </div>
      </section>

      {!loading && analyses.length === 0 && (
        <section className="interview-empty-state">
          <span className="app-page-eyebrow">No match selected</span>
          <h2>Save a match analysis before interview prep.</h2>
          <p>
            The interview needs a resume, target internship, score, and
            requirement evidence.
          </p>
          <Link className="app-primary-action" to="/matches">
            Create match analysis
          </Link>
        </section>
      )}

      {selectedAnalysis && (
        <>
          <section
            className={`interview-settings ${
              mode === 'live' ? 'is-session-active' : ''
            }`}
          >
            <div>
              <span className="app-page-eyebrow">Session settings</span>
              <h2>Choose how you want to be challenged.</h2>
            </div>
            <label>
              Difficulty
              <select
                disabled={working || Boolean(session)}
                onChange={(event) =>
                  setDifficulty(event.target.value as InterviewDifficulty)
                }
                value={difficulty}
              >
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </label>
            <label>
              Questions
              <input
                disabled={working || Boolean(session)}
                max="20"
                min="5"
                onChange={(event) =>
                  setQuestionCount(Number(event.target.value))
                }
                type="number"
                value={questionCount}
              />
            </label>
            <fieldset disabled={working || Boolean(session)}>
              <legend>Focus</legend>
              <div>
                {focusOptions.map((option) => (
                  <button
                    className={
                      focusAreas.includes(option.value) ? 'is-selected' : ''
                    }
                    key={option.value}
                    onClick={() => toggleFocus(option.value)}
                    type="button"
                  >
                    {focusAreas.includes(option.value) && <Check size={13} />}
                    {option.label}
                  </button>
                ))}
              </div>
            </fieldset>
          </section>

          {error && (
            <p className="interview-error" role="alert">
              {error}
            </p>
          )}

          {mode === 'overview' && (
            <>
              <section className="interview-readiness-grid">
                {readiness.map((item) => (
                  <article
                    className={item.available ? 'is-ready' : ''}
                    key={item.label}
                  >
                    <span>{item.available ? 'Ready' : 'Optional'}</span>
                    <h2>{item.label}</h2>
                    <p>{item.description}</p>
                  </article>
                ))}
              </section>

              <section className="interview-mode-grid">
                <ModeCard
                  action={() => void generatePreparation()}
                  available={!working}
                  buttonLabel={working ? 'Generating...' : 'Build question bank'}
                  description="See likely questions, truthful answer structures, supporting evidence, and common mistakes before practicing."
                  icon={<BookOpen size={22} />}
                  steps={[
                    'Role-specific technical questions',
                    'Grounded resume and project evidence',
                    'Answer structures without fabricated claims',
                  ]}
                  title="Question Bank"
                />
                <ModeCard
                  action={() => void startLiveInterview()}
                  available={!working}
                  buttonLabel={working ? 'Starting...' : 'Start live interview'}
                  description="Answer one question at a time. PYXIS keeps its assessment private and presents a collective review at the end."
                  icon={<MessageSquare size={22} />}
                  steps={[
                    'Adaptive follow-up questions',
                    'No distracting scores between answers',
                    'Complete final evaluation and next actions',
                  ]}
                  title="Live Interview"
                />
              </section>

              <ContextBoard
                explanation={explanation}
                githubAnalysis={githubAnalysis}
                learningPaths={learningPaths}
                loading={loadingContext}
                selectedAnalysis={selectedAnalysis}
              />
            </>
          )}

          {mode === 'preparation' && preparation && (
            <PreparationView
              onBack={() => setMode('overview')}
              onRefresh={() => void generatePreparation(true)}
              preparation={preparation}
              refreshing={working}
            />
          )}

          {mode === 'live' && (
            <LiveInterviewView
              answer={answer}
              evaluation={evaluation}
              onAnswerChange={setAnswer}
              onBack={() => setMode('overview')}
              onFinish={() => void finishInterview()}
              onSubmit={() => void submitAnswer()}
              question={question}
              questionsRemaining={questionsRemaining}
              session={session}
              working={working}
            />
          )}
        </>
      )}
    </main>
  )
}

function ModeCard({
  action,
  available,
  buttonLabel,
  description,
  icon,
  steps,
  title,
}: {
  action: () => void
  available: boolean
  buttonLabel: string
  description: string
  icon: React.ReactNode
  steps: string[]
  title: string
}) {
  return (
    <article>
      <div className="interview-mode-heading">
        {icon}
        <span className="app-page-eyebrow">Practice mode</span>
      </div>
      <h2>{title}</h2>
      <p>{description}</p>
      <ul>
        {steps.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ul>
      <button
        className="app-primary-action"
        disabled={!available}
        onClick={action}
        type="button"
      >
        {buttonLabel}
        <ArrowRight size={15} />
      </button>
    </article>
  )
}

function PreparationView({
  onBack,
  onRefresh,
  preparation,
  refreshing,
}: {
  onBack: () => void
  onRefresh: () => void
  preparation: InterviewPreparation
  refreshing: boolean
}) {
  const payload = preparation.preparation_payload
  return (
    <section className="interview-result">
      <header>
        <div>
          <span className="app-page-eyebrow">Question bank</span>
          <h2>{payload.interview_overview}</h2>
          <p>{payload.likely_focus}</p>
        </div>
        <div className="interview-result-actions">
          <button onClick={onBack} type="button">
            Back
          </button>
          <button disabled={refreshing} onClick={onRefresh} type="button">
            <RefreshCw size={14} />
            {refreshing ? 'Refreshing...' : 'Generate fresh'}
          </button>
        </div>
      </header>

      <div className="interview-checklist">
        <strong>Before the interview</strong>
        <ul>
          {payload.preparation_checklist.map((item) => (
            <li key={item}>
              <Check size={14} />
              {item}
            </li>
          ))}
        </ul>
      </div>

      <div className="interview-question-bank">
        {payload.questions.map((item, index) => (
          <details key={`${item.question_text}-${index}`} open={index === 0}>
            <summary>
              <span>{String(index + 1).padStart(2, '0')}</span>
              <div>
                <small>{formatCategory(item.category)}</small>
                <strong>{item.question_text}</strong>
              </div>
            </summary>
            <div className="interview-question-guidance">
              <section>
                <h3>Why it may be asked</h3>
                <p>{item.why_relevant}</p>
              </section>
              <section>
                <h3>How to structure your answer</h3>
                <p>{item.answer_structure}</p>
              </section>
              <ListBlock title="Evidence you can use" values={item.grounded_evidence} />
              <ListBlock title="Avoid these mistakes" values={item.common_mistakes} />
              <ListBlock title="Possible follow-ups" values={item.follow_up_questions} />
            </div>
          </details>
        ))}
      </div>
    </section>
  )
}

function LiveInterviewView({
  answer,
  evaluation,
  onAnswerChange,
  onBack,
  onFinish,
  onSubmit,
  question,
  questionsRemaining,
  session,
  working,
}: {
  answer: string
  evaluation: InterviewEvaluation | null
  onAnswerChange: (value: string) => void
  onBack: () => void
  onFinish: () => void
  onSubmit: () => void
  question: InterviewQuestion | null
  questionsRemaining: number
  session: InterviewSession | null
  working: boolean
}) {
  if (evaluation) {
    return <EvaluationView evaluation={evaluation} onBack={onBack} />
  }

  return (
    <section className="live-interview">
      <header>
        <div>
          <span className="app-page-eyebrow">Live interview</span>
          <h2>
            {question?.is_follow_up
              ? `Follow-up to question ${question.sequence_number}`
              : `Question ${question?.sequence_number ?? 1}`}
          </h2>
        </div>
        <div className="live-progress">
          <strong>{questionsRemaining}</strong>
          <span>planned questions remaining</span>
        </div>
      </header>

      {question && (
        <article className="live-question-card">
          <div>
            <span>{formatCategory(question.category)}</span>
            {question.is_follow_up && <em>Adaptive follow-up</em>}
          </div>
          <h3>{question.question_text}</h3>
          <p>{question.reason}</p>
        </article>
      )}

      <label className="live-answer">
        Your answer
        <textarea
          disabled={working}
          maxLength={4000}
          onChange={(event) => onAnswerChange(event.target.value)}
          placeholder="Answer as you would in a real interview. Use concrete evidence from your work where possible."
          rows={6}
          value={answer}
        />
        <span>{answer.length}/4000 · minimum 10 characters</span>
      </label>

      <div className="live-actions">
        <button
          className="app-primary-action"
          disabled={working || answer.trim().length < 10}
          onClick={onSubmit}
          type="button"
        >
          <Send size={15} />
          {working ? 'Reviewing answer...' : 'Submit and continue'}
        </button>
        {session && question && (
          <button disabled={working} onClick={onFinish} type="button">
            <Flag size={14} />
            Finish interview
          </button>
        )}
      </div>
      <p className="live-privacy-note">
        PYXIS stores its per-answer assessment privately. Your feedback appears
        only when the interview ends.
      </p>
    </section>
  )
}

function EvaluationView({
  evaluation,
  onBack,
}: {
  evaluation: InterviewEvaluation
  onBack: () => void
}) {
  const result = evaluation.evaluation
  return (
    <section className="interview-evaluation">
      <header>
        <div>
          <span className="app-page-eyebrow">Final interview review</span>
          <h2>{result.verdict}</h2>
          <p>{result.summary}</p>
        </div>
        <strong>{Math.round(result.overall_score)}%</strong>
      </header>

      <div className="evaluation-category-grid">
        {result.category_scores.map((category) => (
          <article key={category.category}>
            <span>{formatCategory(category.category)}</span>
            <strong>{Math.round(category.score)}%</strong>
            <p>{category.improvements[0] ?? category.strengths[0]}</p>
          </article>
        ))}
      </div>

      <div className="evaluation-summary-grid">
        <ListBlock
          title="Demonstrated strengths"
          values={result.demonstrated_strengths}
        />
        <ListBlock title="Knowledge gaps" values={result.knowledge_gaps} />
        <ListBlock
          title="Communication feedback"
          values={result.communication_feedback}
        />
        <ListBlock title="Next actions" values={result.next_actions} />
      </div>

      <div className="evaluation-reviews">
        <h3>Question-by-question review</h3>
        {result.question_reviews.map((review, index) => (
          <details key={review.question_id}>
            <summary>
              <span>{String(index + 1).padStart(2, '0')}</span>
              <strong>{review.question}</strong>
              <em>{Math.round(review.score)}%</em>
            </summary>
            <div>
              <p>{review.answer_summary}</p>
              <ListBlock title="What worked" values={review.what_went_well} />
              <ListBlock title="What was missing" values={review.what_was_missing} />
              <section>
                <h4>Better answer approach</h4>
                <p>{review.better_answer_approach}</p>
              </section>
            </div>
          </details>
        ))}
      </div>

      <button className="app-primary-action" onClick={onBack} type="button">
        Return to interview modes
      </button>
    </section>
  )
}

function ContextBoard({
  explanation,
  githubAnalysis,
  learningPaths,
  loading,
  selectedAnalysis,
}: {
  explanation: MatchExplanation | null
  githubAnalysis: GitHubProfileAnalysis | null
  learningPaths: MatchLearningPaths | null
  loading: boolean
  selectedAnalysis: MatchAnalysis
}) {
  const gaps = explanation?.explanation.gaps.slice(0, 4) ?? []
  const talkingPoints =
    explanation?.explanation.interview_talking_points.slice(0, 4) ?? []
  const pathTargets =
    learningPaths?.learning_paths
      .map((path) => path.target_skill)
      .slice(0, 5) ?? []

  return (
    <section className="interview-context-layout">
      <article>
        <span className="app-page-eyebrow">Preparation board</span>
        <h2>{loading ? 'Loading context...' : 'What PYXIS will prepare from'}</h2>
        <div className="interview-context-list">
          <section>
            <strong>Match summary</strong>
            <p>
              {Math.round(selectedAnalysis.overall_score)}% saved match with
              structured requirement evidence.
            </p>
          </section>
          <section>
            <strong>AI explanation</strong>
            <p>
              {explanation
                ? explanation.explanation.score_card.headline
                : 'Optional. The base match can still generate an interview.'}
            </p>
          </section>
          <section>
            <strong>Likely talking points</strong>
            <ul>
              {talkingPoints.length ? (
                talkingPoints.map((point) => (
                  <li key={`${point.requirement}-${point.prompt}`}>
                    {point.requirement}: {point.prompt}
                  </li>
                ))
              ) : (
                <li>Role requirements and resume evidence from the saved match.</li>
              )}
            </ul>
          </section>
          <section>
            <strong>Gap focus</strong>
            <p>
              {gaps.length
                ? gaps.map((gap) => gap.requirement).join(', ')
                : 'The base match will supply missing requirements.'}
            </p>
          </section>
          <section>
            <strong>Learning targets</strong>
            <p>
              {pathTargets.length
                ? pathTargets.join(', ')
                : 'No graph learning targets available.'}
            </p>
          </section>
          <section>
            <strong>GitHub profile</strong>
            <p>
              {githubAnalysis
                ? `${githubAnalysis.github_username}: profile review available. Match-specific GitHub evidence remains optional.`
                : 'Optional. Interviews work without GitHub evidence.'}
            </p>
          </section>
        </div>
      </article>
      <article>
        <span className="app-page-eyebrow">What happens</span>
        <h2>Feedback stays out of your way.</h2>
        <div className="interview-practice-list">
          {[
            ['Prepare', 'PYXIS builds a compact context from your selected match.'],
            ['Answer', 'Live mode asks one grounded question at a time.'],
            ['Adapt', 'A weak or unclear answer may trigger one follow-up.'],
            ['Review', 'Your full assessment appears only after completion.'],
          ].map(([title, description]) => (
            <section key={title}>
              <strong>{title}</strong>
              <p>{description}</p>
            </section>
          ))}
        </div>
      </article>
    </section>
  )
}

function ListBlock({ title, values }: { title: string; values: string[] }) {
  if (!values.length) return null
  return (
    <section className="interview-list-block">
      <h3>{title}</h3>
      <ul>
        {values.map((value) => (
          <li key={value}>{value}</li>
        ))}
      </ul>
    </section>
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
      description: 'Core score, requirements, and selected resume evidence.',
      label: 'Saved match',
    },
    {
      available: Boolean(explanation),
      description: 'Strengths, gaps, improvements, and talking points.',
      label: 'AI explanation',
    },
    {
      available: Boolean(learningPaths?.learning_paths.length),
      description: 'Graph-backed gaps available on the preparation board.',
      label: 'Learning paths',
    },
    {
      available: Boolean(githubAnalysis),
      description: 'Profile review available; match evidence remains optional.',
      label: 'GitHub context',
    },
  ]
}

function formatCategory(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) =>
    letter.toUpperCase(),
  )
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function errorMessage(error: unknown) {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'The interview request could not be completed.'
}
