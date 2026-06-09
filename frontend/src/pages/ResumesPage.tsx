import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
} from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../lib/api'
import {
  getCachedResumes,
  loadResumes,
  retryResume,
  uploadResume,
} from '../lib/resumes'
import type { Resume, ResumeProcessingStatus } from '../types/resume'
import './Resumes.css'

const activeStatuses: ResumeProcessingStatus[] = [
  'uploaded',
  'extracting_text',
  'text_extracted',
  'parsing',
  'validating',
  'embedding',
]

const statusLabels: Record<ResumeProcessingStatus, string> = {
  uploaded: 'Queued',
  extracting_text: 'Extracting text',
  text_extracted: 'Text extracted',
  parsing: 'Parsing profile',
  validating: 'Validating',
  embedding: 'Creating evidence',
  ready: 'Ready',
  failed: 'Needs attention',
}

export function ResumesPage() {
  const cached = getCachedResumes()
  const [resumes, setResumes] = useState<Resume[]>(cached ?? [])
  const [loading, setLoading] = useState(!cached)
  const [error, setError] = useState('')
  const [uploadOpen, setUploadOpen] = useState(false)
  const [retryingId, setRetryingId] = useState<string | null>(null)

  const refresh = useCallback(async (force = false) => {
    try {
      setError('')
      const result = await loadResumes(force)
      setResumes(result)
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : 'The resume library could not be loaded.',
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true

    loadResumes()
      .then((result) => {
        if (active) {
          setResumes(result)
          setError('')
        }
      })
      .catch((requestError) => {
        if (active) {
          setError(
            requestError instanceof ApiError
              ? requestError.message
              : 'The resume library could not be loaded.',
          )
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  const hasActiveProcessing = resumes.some((resume) =>
    activeStatuses.includes(resume.processing_status),
  )

  useEffect(() => {
    if (!hasActiveProcessing) return

    const interval = window.setInterval(() => {
      void refresh(true)
    }, 5000)

    return () => window.clearInterval(interval)
  }, [hasActiveProcessing, refresh])

  const counts = useMemo(
    () => ({
      total: resumes.length,
      ready: resumes.filter((resume) => resume.processing_status === 'ready')
        .length,
      processing: resumes.filter((resume) =>
        activeStatuses.includes(resume.processing_status),
      ).length,
      failed: resumes.filter((resume) => resume.processing_status === 'failed')
        .length,
    }),
    [resumes],
  )

  async function handleRetry(resumeId: string) {
    try {
      setRetryingId(resumeId)
      setError('')
      const resumed = await retryResume(resumeId)
      setResumes((current) =>
        current.map((resume) => (resume.id === resumed.id ? resumed : resume)),
      )
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : 'Resume processing could not be retried.',
      )
    } finally {
      setRetryingId(null)
    }
  }

  function handleUploaded(resume: Resume) {
    setResumes((current) => [
      resume,
      ...current.filter((item) => item.id !== resume.id),
    ])
    setUploadOpen(false)
  }

  return (
    <main className="app-page resumes-page">
      <header className="app-page-header">
        <div>
          <span className="app-page-eyebrow">Profile evidence</span>
          <h1>Resume library</h1>
          <p>
            Every resume is parsed into reusable profile evidence. Processing
            states update automatically while the backend worker is active.
          </p>
        </div>
        <button
          className="app-primary-action"
          onClick={() => setUploadOpen(true)}
          type="button"
        >
          Upload resume
        </button>
      </header>

      <section className="resume-summary" aria-label="Resume summary">
        <SummaryCell label="Total resumes" value={counts.total} />
        <SummaryCell label="Ready" value={counts.ready} />
        <SummaryCell label="Processing" value={counts.processing} />
        <SummaryCell label="Needs attention" value={counts.failed} />
      </section>

      <section className="resume-library">
        <div className="resume-library-header">
          <div>
            <h2>Your resumes</h2>
            <p>Saved documents and their current processing state.</p>
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

        {error && (
          <div className="resume-message is-error">
            <div>
              <strong>Unable to load resumes</strong>
              <p>{error}</p>
            </div>
            <button onClick={() => void refresh(true)} type="button">
              Try again
            </button>
          </div>
        )}

        {loading && resumes.length === 0 && <ResumeSkeleton />}

        {!loading && !error && resumes.length === 0 && (
          <div className="resume-empty">
            <span>01 / EMPTY LIBRARY</span>
            <h3>Your resume evidence will appear here.</h3>
            <p>
              Upload a resume to extract skills, projects, education,
              certifications, and profile facts for matching.
            </p>
            <button
              className="app-primary-action"
              onClick={() => setUploadOpen(true)}
              type="button"
            >
              Upload first resume
            </button>
          </div>
        )}

        {resumes.length > 0 && (
          <div className="resume-table-wrap">
            <table className="resume-table">
              <thead>
                <tr>
                  <th>Resume</th>
                  <th>Status</th>
                  <th>Uploaded</th>
                  <th>Size</th>
                </tr>
              </thead>
              <tbody>
                {resumes.map((resume) => (
                  <tr key={resume.id}>
                    <td>
                      <Link
                        className="resume-name"
                        to={`/resumes/${resume.id}`}
                      >
                        <span>PDF</span>
                        <div>
                          <strong>{resume.alias}</strong>
                          <small>
                            {resume.original_filename}
                            {resume.is_default ? ' · Default' : ''}
                          </small>
                        </div>
                      </Link>
                    </td>
                    <td>
                      <span
                        className={`resume-status is-${resume.processing_status}`}
                      >
                        {statusLabels[resume.processing_status]}
                      </span>
                      {resume.processing_error && (
                        <small className="resume-error">
                          {resume.processing_error}
                        </small>
                      )}
                      {resume.processing_status === 'failed' && (
                        <button
                          className="resume-retry"
                          disabled={retryingId === resume.id}
                          onClick={() => void handleRetry(resume.id)}
                          type="button"
                        >
                          {retryingId === resume.id
                            ? 'Retrying...'
                            : 'Retry processing'}
                        </button>
                      )}
                    </td>
                    <td>{formatDate(resume.created_at)}</td>
                    <td>{formatFileSize(resume.file_size_bytes)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {uploadOpen && (
        <ResumeUploadDialog
          onClose={() => setUploadOpen(false)}
          onUploaded={handleUploaded}
        />
      )}
    </main>
  )
}

function ResumeUploadDialog({
  onClose,
  onUploaded,
}: {
  onClose: () => void
  onUploaded: (resume: Resume) => void
}) {
  const fileInput = useRef<HTMLInputElement>(null)
  const [alias, setAlias] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!file) {
      setError('Select a PDF or DOCX resume first.')
      return
    }

    try {
      setSubmitting(true)
      setError('')
      const resume = await uploadResume(alias.trim(), file)
      onUploaded(resume)
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : 'The resume could not be uploaded.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  function chooseFile(selectedFile: File | null) {
    setFile(selectedFile)
    if (selectedFile && !alias) {
      setAlias(selectedFile.name.replace(/\.(pdf|docx)$/i, ''))
    }
  }

  return (
    <div className="resume-dialog-backdrop" role="presentation">
      <section
        aria-labelledby="resume-upload-title"
        aria-modal="true"
        className="resume-dialog"
        role="dialog"
      >
        <div className="resume-dialog-header">
          <div>
            <span className="app-page-eyebrow">New profile evidence</span>
            <h2 id="resume-upload-title">Upload a resume</h2>
          </div>
          <button
            aria-label="Close upload dialog"
            disabled={submitting}
            onClick={onClose}
            type="button"
          >
            Close
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <button
            className={`resume-file-drop ${file ? 'has-file' : ''}`}
            onClick={() => fileInput.current?.click()}
            type="button"
          >
            <span>{file ? file.name : 'Choose PDF or DOCX'}</span>
            <small>
              {file
                ? `${formatFileSize(file.size)} selected`
                : 'Maximum file size: 10 MB'}
            </small>
          </button>
          <input
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            className="visually-hidden"
            onChange={(event) => chooseFile(event.target.files?.[0] ?? null)}
            ref={fileInput}
            type="file"
          />

          <label className="resume-alias-field">
            <span>Resume name</span>
            <input
              maxLength={80}
              onChange={(event) => setAlias(event.target.value)}
              placeholder="e.g. Cybersecurity resume"
              required
              value={alias}
            />
          </label>

          {error && <p className="resume-upload-error">{error}</p>}

          <div className="resume-dialog-actions">
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
              disabled={submitting || !file || !alias.trim()}
              type="submit"
            >
              {submitting ? 'Uploading...' : 'Upload and process'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

function SummaryCell({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function ResumeSkeleton() {
  return (
    <div className="resume-skeleton" aria-label="Loading resumes">
      <span />
      <span />
      <span />
    </div>
  )
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date(value))
}

function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
