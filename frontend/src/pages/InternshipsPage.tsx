import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../lib/api'
import {
  createInternship,
  deleteInternship,
  getCachedInternships,
  loadInternships,
  reparseInternship,
  retryInternship,
} from '../lib/internships'
import type {
  Internship,
  InternshipProcessingStatus,
} from '../types/internship'
import './Internships.css'

const activeStatuses: InternshipProcessingStatus[] = [
  'submitted',
  'parsing',
  'validating',
]

const statusLabels: Record<InternshipProcessingStatus, string> = {
  submitted: 'Queued',
  parsing: 'Parsing',
  validating: 'Validating',
  ready: 'Ready',
  failed: 'Needs attention',
}

export function InternshipsPage() {
  const cached = getCachedInternships()
  const [internships, setInternships] = useState<Internship[]>(cached ?? [])
  const [loading, setLoading] = useState(!cached)
  const [error, setError] = useState('')
  const [createOpen, setCreateOpen] = useState(false)
  const [workingId, setWorkingId] = useState<string | null>(null)

  const refresh = useCallback(async (force = false) => {
    try {
      setError('')
      setInternships(await loadInternships(force))
    } catch (requestError) {
      setError(messageFrom(requestError, 'Internships could not be loaded.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    loadInternships()
      .then((result) => {
        if (active) setInternships(result)
      })
      .catch((requestError) => {
        if (active) {
          setError(messageFrom(requestError, 'Internships could not be loaded.'))
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  const hasActiveProcessing = internships.some((internship) =>
    activeStatuses.includes(internship.processing_status),
  )

  useEffect(() => {
    if (!hasActiveProcessing) return
    const interval = window.setInterval(() => void refresh(true), 5000)
    return () => window.clearInterval(interval)
  }, [hasActiveProcessing, refresh])

  const counts = useMemo(
    () => ({
      total: internships.length,
      ready: internships.filter((item) => item.processing_status === 'ready')
        .length,
      processing: internships.filter((item) =>
        activeStatuses.includes(item.processing_status),
      ).length,
      failed: internships.filter((item) => item.processing_status === 'failed')
        .length,
    }),
    [internships],
  )

  async function runAction(
    internship: Internship,
    action: 'retry' | 'reparse' | 'delete',
  ) {
    if (
      action === 'delete' &&
      !window.confirm(`Delete "${internship.label}"? This cannot be undone.`)
    ) {
      return
    }

    try {
      setWorkingId(internship.id)
      setError('')
      if (action === 'delete') {
        await deleteInternship(internship.id)
        setInternships((current) =>
          current.filter((item) => item.id !== internship.id),
        )
        return
      }

      const updated =
        action === 'retry'
          ? await retryInternship(internship.id)
          : await reparseInternship(internship.id)
      setInternships((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      )
    } catch (requestError) {
      setError(messageFrom(requestError, `Unable to ${action} internship.`))
    } finally {
      setWorkingId(null)
    }
  }

  return (
    <main className="app-page internships-page">
      <header className="app-page-header">
        <div>
          <span className="app-page-eyebrow">Role requirements</span>
          <h1>Internship library</h1>
          <p>
            Save target roles once, let the parser structure their
            requirements, and reuse them across resume analyses.
          </p>
        </div>
        <button
          className="app-primary-action"
          onClick={() => setCreateOpen(true)}
          type="button"
        >
          Add internship
        </button>
      </header>

      <section className="internship-summary">
        <Summary label="Saved roles" value={counts.total} />
        <Summary label="Ready" value={counts.ready} />
        <Summary label="Processing" value={counts.processing} />
        <Summary label="Needs attention" value={counts.failed} />
      </section>

      <section className="internship-library">
        <div className="internship-library-header">
          <div>
            <h2>Your target roles</h2>
            <p>Parsed internship descriptions available for matching.</p>
          </div>
          <button
            className="app-secondary-action"
            disabled={loading}
            onClick={() => void refresh(true)}
            type="button"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {error && <div className="internship-error">{error}</div>}
        {loading && internships.length === 0 && (
          <div className="internship-loading">Loading internships...</div>
        )}
        {!loading && internships.length === 0 && (
          <div className="internship-empty">
            <span>01 / NO TARGET ROLES</span>
            <h3>Add the internship you want to understand.</h3>
            <p>
              Paste the complete job description so required and preferred
              evidence can be separated accurately.
            </p>
            <button
              className="app-primary-action"
              onClick={() => setCreateOpen(true)}
              type="button"
            >
              Add first internship
            </button>
          </div>
        )}

        {internships.length > 0 && (
          <div className="internship-list">
            {internships.map((internship) => (
              <article key={internship.id}>
                <Link
                  className="internship-main"
                  to={`/internships/${internship.id}`}
                >
                  <span className="internship-document">ROLE</span>
                  <div>
                    <h3>{internship.label}</h3>
                    <p>
                      Added {formatDate(internship.created_at)}
                      {internship.application_url ? ' · Application linked' : ''}
                    </p>
                  </div>
                </Link>
                <div className="internship-state">
                  <span className={`is-${internship.processing_status}`}>
                    {statusLabels[internship.processing_status]}
                  </span>
                  {internship.processing_error && (
                    <small>{internship.processing_error}</small>
                  )}
                </div>
                <div className="internship-actions">
                  {internship.processing_status === 'failed' && (
                    <button
                      disabled={workingId === internship.id}
                      onClick={() => void runAction(internship, 'retry')}
                      type="button"
                    >
                      Retry
                    </button>
                  )}
                  {internship.processing_status === 'ready' && (
                    <button
                      disabled={workingId === internship.id}
                      onClick={() => void runAction(internship, 'reparse')}
                      type="button"
                    >
                      Reparse
                    </button>
                  )}
                  <button
                    className="is-danger"
                    disabled={workingId === internship.id}
                    onClick={() => void runAction(internship, 'delete')}
                    type="button"
                  >
                    Delete
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      {createOpen && (
        <CreateInternshipDialog
          onClose={() => setCreateOpen(false)}
          onCreated={(internship) => {
            setInternships((current) => [
              internship,
              ...current.filter((item) => item.id !== internship.id),
            ])
            setCreateOpen(false)
          }}
        />
      )}
    </main>
  )
}

function CreateInternshipDialog({
  onClose,
  onCreated,
}: {
  onClose: () => void
  onCreated: (internship: Internship) => void
}) {
  const [label, setLabel] = useState('')
  const [description, setDescription] = useState('')
  const [applicationUrl, setApplicationUrl] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try {
      setSubmitting(true)
      setError('')
      onCreated(
        await createInternship({
          label: label.trim(),
          original_description: description.trim(),
          application_url: applicationUrl.trim() || null,
        }),
      )
    } catch (requestError) {
      setError(messageFrom(requestError, 'The internship could not be saved.'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="internship-dialog-backdrop">
      <section
        aria-labelledby="internship-dialog-title"
        aria-modal="true"
        className="internship-dialog"
        role="dialog"
      >
        <div className="internship-dialog-header">
          <div>
            <span className="app-page-eyebrow">New target role</span>
            <h2 id="internship-dialog-title">Add an internship</h2>
          </div>
          <button disabled={submitting} onClick={onClose} type="button">
            Close
          </button>
        </div>
        <form onSubmit={submit}>
          <label>
            <span>Role label</span>
            <input
              maxLength={120}
              onChange={(event) => setLabel(event.target.value)}
              placeholder="e.g. SOC Analyst Intern"
              required
              value={label}
            />
          </label>
          <label>
            <span>Job description</span>
            <textarea
              maxLength={20000}
              minLength={50}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Paste the complete internship description..."
              required
              value={description}
            />
            <small>{description.length.toLocaleString()} / 20,000</small>
          </label>
          <label>
            <span>Application URL (optional)</span>
            <input
              onChange={(event) => setApplicationUrl(event.target.value)}
              placeholder="https://..."
              type="url"
              value={applicationUrl}
            />
          </label>
          {error && <p className="internship-form-error">{error}</p>}
          <div className="internship-dialog-actions">
            <button
              className="app-secondary-action"
              disabled={submitting}
              onClick={onClose}
              type="button"
            >
              Cancel
            </button>
            <button
              className="app-primary-action"
              disabled={
                submitting || !label.trim() || description.trim().length < 50
              }
              type="submit"
            >
              {submitting ? 'Saving...' : 'Save and parse'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

function Summary({ label, value }: { label: string; value: number }) {
  return <div><span>{label}</span><strong>{value}</strong></div>
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date(value))
}

function messageFrom(error: unknown, fallback: string) {
  return error instanceof ApiError ? error.message : fallback
}
