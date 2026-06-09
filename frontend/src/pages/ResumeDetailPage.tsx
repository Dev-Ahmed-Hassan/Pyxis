import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  ConfidenceBar,
  DataDonut,
  EvidenceDisclosure,
} from '../components/DataVisuals'
import { ApiError } from '../lib/api'
import {
  getCachedResumes,
  getParsedResumeProfile,
  getResume,
} from '../lib/resumes'
import type { ParsedResumeProfile, Resume } from '../types/resume'
import './ResumeDetail.css'

export function ResumeDetailPage() {
  const { resumeId = '' } = useParams()
  const cachedResume = getCachedResumes()?.find(
    (resume) => resume.id === resumeId,
  )
  const [resume, setResume] = useState<Resume | null>(cachedResume ?? null)
  const [profile, setProfile] = useState<ParsedResumeProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    async function loadDetail() {
      try {
        setError('')
        const currentResume = resume ?? (await getResume(resumeId))
        if (!active) return
        setResume(currentResume)

        if (currentResume.processing_status === 'ready') {
          const parsedProfile = await getParsedResumeProfile(resumeId)
          if (active) setProfile(parsedProfile)
        }
      } catch (requestError) {
        if (active) {
          setError(
            requestError instanceof ApiError
              ? requestError.message
              : 'The resume profile could not be loaded.',
          )
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    void loadDetail()
    return () => {
      active = false
    }
  }, [resume, resumeId])

  if (loading) {
    return (
      <main className="app-page resume-detail-page">
        <Link className="resume-back-link" to="/resumes">Back to resumes</Link>
        <div className="resume-detail-loading">Loading parsed evidence...</div>
      </main>
    )
  }

  if (error || !resume) {
    return (
      <main className="app-page resume-detail-page">
        <Link className="resume-back-link" to="/resumes">Back to resumes</Link>
        <div className="resume-detail-message">
          <h1>Resume unavailable</h1>
          <p>{error || 'This resume could not be found.'}</p>
        </div>
      </main>
    )
  }

  if (resume.processing_status !== 'ready' || !profile) {
    return (
      <main className="app-page resume-detail-page">
        <Link className="resume-back-link" to="/resumes">Back to resumes</Link>
        <div className="resume-detail-message">
          <span className="app-page-eyebrow">Processing status</span>
          <h1>{resume.alias}</h1>
          <p>
            Parsed evidence becomes available when this resume reaches the
            ready state. Its current status is{' '}
            <strong>{resume.processing_status.replaceAll('_', ' ')}</strong>.
          </p>
        </div>
      </main>
    )
  }

  const parsed = profile.parsed_resume
  const sourceCounts = parsed.skills.reduce(
    (counts, skill) => {
      counts[skill.source] += 1
      return counts
    },
    { explicit: 0, inferred: 0, manual: 0 },
  )
  const identityFields = [
    parsed.full_name,
    parsed.email,
    parsed.phone,
    parsed.location,
    parsed.summary,
  ]
  const averageIdentityConfidence =
    identityFields.reduce((total, field) => total + field.confidence, 0) /
    identityFields.length

  return (
    <main className="app-page resume-detail-page">
      <Link className="resume-back-link" to="/resumes">Back to resumes</Link>

      <header className="resume-profile-header">
        <div>
          <span className="app-page-eyebrow">Parsed resume evidence</span>
          <h1>{parsed.full_name.value || resume.alias}</h1>
          <p>{parsed.summary.value || 'No professional summary was extracted.'}</p>
          <div className="resume-detail-actions">
            <Link className="app-secondary-action" to="/internships">
              Add or review internships
            </Link>
            <Link className="app-primary-action" to="/matches">
              Use in match analysis
            </Link>
          </div>
        </div>
        <dl>
          <ProfileFact
            confidence={parsed.email.confidence}
            label="Email"
            provenance={profile.field_provenance.email}
            value={parsed.email.value}
          />
          <ProfileFact
            confidence={parsed.phone.confidence}
            label="Phone"
            provenance={profile.field_provenance.phone}
            value={parsed.phone.value}
          />
          <ProfileFact
            confidence={parsed.location.confidence}
            label="Location"
            provenance={profile.field_provenance.location}
            value={parsed.location.value}
          />
          <ProfileFact label="Source" value={resume.original_filename} />
        </dl>
      </header>

      <section className="resume-data-overview">
        <article>
          <span className="app-page-eyebrow">Skill source</span>
          <h2>How capabilities were identified</h2>
          <DataDonut
            data={[
              { name: 'Explicit', value: sourceCounts.explicit, color: '#123b32' },
              { name: 'Inferred', value: sourceCounts.inferred, color: '#8ca99f' },
              { name: 'Manual', value: sourceCounts.manual, color: '#d2c7ad' },
            ]}
            label="skills"
            total={parsed.skills.length}
          />
        </article>
        <article>
          <span className="app-page-eyebrow">Extraction quality</span>
          <h2>Profile signal summary</h2>
          <ConfidenceBar confidence={averageIdentityConfidence} />
          <div className="resume-signal-stats">
            <div><strong>{parsed.projects.length}</strong><span>Projects</span></div>
            <div><strong>{parsed.experience.length}</strong><span>Roles</span></div>
            <div><strong>{parsed.certifications.length}</strong><span>Certifications</span></div>
            <div><strong>{parsed.review_warnings.length}</strong><span>Warnings</span></div>
          </div>
        </article>
      </section>

      <section className="resume-profile-section">
        <SectionHeading
          count={parsed.skills.length}
          label="Skills"
          title="Extracted capabilities"
        />
        <div className="resume-skill-list">
          {parsed.skills.map((skill, index) => (
            <article className="resume-skill-card" key={`${skill.name}-${index}`}>
              <div>
                <strong>{skill.canonical_name || skill.name}</strong>
                <span>{skill.source}</span>
              </div>
              {skill.canonical_name && skill.canonical_name !== skill.name && (
                <small>Original: {skill.name}</small>
              )}
              <EvidenceDisclosure
                confidence={skill.confidence}
                evidence={skill.evidence}
                source={skill.source}
              />
            </article>
          ))}
        </div>
      </section>

      <ProfileCollection
        empty="No experience entries were extracted."
        items={parsed.experience.map((experience) => ({
          title: experience.role || 'Untitled role',
          meta: [experience.company, dateRange(experience.start_date, experience.end_date)]
            .filter(Boolean)
            .join(' · '),
          lines: experience.description,
          skills: experience.skills,
          confidence: experience.confidence,
          evidence: experience.evidence,
        }))}
        label="Experience"
        title="Professional evidence"
      />

      <ProfileCollection
        empty="No projects were extracted."
        items={parsed.projects.map((project) => ({
          title: project.name || 'Untitled project',
          meta: 'Resume project',
          lines: project.description,
          skills: project.skills,
          confidence: project.confidence,
          evidence: project.evidence,
        }))}
        label="Projects"
        title="Built work"
      />

      <section className="resume-profile-columns">
        <div className="resume-profile-section">
          <SectionHeading
            count={parsed.education.length}
            label="Education"
            title="Academic background"
          />
          <div className="resume-compact-list">
            {parsed.education.map((education, index) => (
              <article key={`${education.institution}-${index}`}>
                <h3>{education.degree || 'Education'}</h3>
                <p>
                  {[education.field_of_study, education.institution]
                    .filter(Boolean)
                    .join(' · ')}
                </p>
                <small>{dateRange(education.start_date, education.end_date)}</small>
                <EvidenceDisclosure
                  confidence={education.confidence}
                  evidence={education.evidence}
                />
              </article>
            ))}
          </div>
        </div>

        <div className="resume-profile-section">
          <SectionHeading
            count={parsed.certifications.length}
            label="Certifications"
            title="Verified learning"
          />
          <div className="resume-compact-list">
            {parsed.certifications.map((certification, index) => (
              <article key={`${certification.name}-${index}`}>
                <h3>{certification.name}</h3>
                <p>{certification.issuer || 'Issuer not specified'}</p>
                <small>{certification.date || 'Date not specified'}</small>
                <EvidenceDisclosure
                  confidence={certification.confidence}
                  evidence={certification.evidence}
                />
              </article>
            ))}
          </div>
        </div>
      </section>

      {parsed.review_warnings.length > 0 && (
        <section className="resume-profile-section resume-review-warnings">
          <SectionHeading
            count={parsed.review_warnings.length}
            label="Review"
            title="Items worth checking"
          />
          {parsed.review_warnings.map((warning, index) => (
            <article key={`${warning.field}-${index}`}>
              <strong>{warning.field.replaceAll('_', ' ')}</strong>
              <p>{warning.message}</p>
            </article>
          ))}
        </section>
      )}
    </main>
  )
}

function ProfileFact({
  confidence,
  label,
  provenance,
  value,
}: {
  confidence?: number
  label: string
  provenance?: string
  value: string | null
}) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>
        {value || 'Not found'}
        {(provenance || confidence !== undefined) && (
          <small>
            {provenance?.replaceAll('_', ' ')}
            {provenance && confidence !== undefined ? ' · ' : ''}
            {confidence !== undefined
              ? `${Math.round(confidence * 100)}% confidence`
              : ''}
          </small>
        )}
      </dd>
    </div>
  )
}

function SectionHeading({
  count,
  label,
  title,
}: {
  count: number
  label: string
  title: string
}) {
  return (
    <header className="resume-section-heading">
      <div>
        <span className="app-page-eyebrow">{label}</span>
        <h2>{title}</h2>
      </div>
      <strong>{String(count).padStart(2, '0')}</strong>
    </header>
  )
}

function ProfileCollection({
  empty,
  items,
  label,
  title,
}: {
  empty: string
  items: Array<{
    title: string
    meta: string
    lines: string[]
    skills: ParsedResumeProfile['parsed_resume']['skills']
    confidence: number
    evidence: string | null
  }>
  label: string
  title: string
}) {
  return (
    <section className="resume-profile-section">
      <SectionHeading count={items.length} label={label} title={title} />
      {items.length === 0 ? (
        <p className="resume-profile-empty">{empty}</p>
      ) : (
        <div className="resume-entry-list">
          {items.map((item, index) => (
            <article key={`${item.title}-${index}`}>
              <div className="resume-entry-title">
                <h3>{item.title}</h3>
                <span>{item.meta}</span>
              </div>
              {item.lines.length > 0 && (
                <ul>
                  {item.lines.map((line, lineIndex) => (
                    <li key={`${line}-${lineIndex}`}>{line}</li>
                  ))}
                </ul>
              )}
              {item.skills.length > 0 && (
                <div className="resume-entry-skills">
                  {item.skills.map((skill, skillIndex) => (
                    <span key={`${skill.name}-${skillIndex}`}>
                      {skill.canonical_name || skill.name}
                    </span>
                  ))}
                </div>
              )}
              <EvidenceDisclosure
                confidence={item.confidence}
                evidence={item.evidence}
              />
            </article>
          ))}
        </div>
      )}
    </section>
  )
}

function dateRange(start: string | null, end: string | null) {
  if (!start && !end) return ''
  return [start || 'Unknown', end || 'Present'].join(' – ')
}
