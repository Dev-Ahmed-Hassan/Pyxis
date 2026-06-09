import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  DataDonut,
  EvidenceDisclosure,
} from '../components/DataVisuals'
import { ApiError } from '../lib/api'
import {
  getCachedInternships,
  getInternship,
  getParsedInternshipRequirements,
} from '../lib/internships'
import type {
  Internship,
  ParsedInternshipRequirements,
} from '../types/internship'
import type { ExtractedSkill } from '../types/resume'
import './InternshipDetail.css'

export function InternshipDetailPage() {
  const { internshipId = '' } = useParams()
  const cached = getCachedInternships()?.find(
    (internship) => internship.id === internshipId,
  )
  const [internship, setInternship] = useState<Internship | null>(cached ?? null)
  const [requirements, setRequirements] =
    useState<ParsedInternshipRequirements | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    async function load() {
      try {
        const current = internship ?? (await getInternship(internshipId))
        if (!active) return
        setInternship(current)
        if (current.processing_status === 'ready') {
          const parsed = await getParsedInternshipRequirements(internshipId)
          if (active) setRequirements(parsed)
        }
      } catch (requestError) {
        if (active) {
          setError(
            requestError instanceof ApiError
              ? requestError.message
              : 'Internship requirements could not be loaded.',
          )
        }
      } finally {
        if (active) setLoading(false)
      }
    }

    void load()
    return () => {
      active = false
    }
  }, [internship, internshipId])

  if (loading) {
    return <DetailMessage message="Loading parsed requirements..." />
  }

  if (error || !internship) {
    return <DetailMessage message={error || 'Internship not found.'} />
  }

  if (internship.processing_status !== 'ready' || !requirements) {
    return (
      <DetailMessage
        message={`Requirements become available when parsing is ready. Current status: ${internship.processing_status}.`}
        title={internship.label}
      />
    )
  }

  const parsed = requirements.parsed_internship
  const requiredTotal =
    parsed.required_skills.length +
    parsed.required_domain_concepts.length +
    parsed.required_soft_skills.length
  const preferredTotal =
    parsed.preferred_skills.length +
    parsed.preferred_domain_concepts.length +
    parsed.preferred_soft_skills.length
  const technicalTotal =
    parsed.required_skills.length + parsed.preferred_skills.length
  const domainTotal =
    parsed.required_domain_concepts.length +
    parsed.preferred_domain_concepts.length
  const softTotal =
    parsed.required_soft_skills.length + parsed.preferred_soft_skills.length

  return (
    <main className="app-page internship-detail-page">
      <Link className="internship-back-link" to="/internships">
        Back to internships
      </Link>

      <header className="internship-profile-header">
        <div>
          <span className="app-page-eyebrow">Parsed role requirements</span>
          <h1>{parsed.title.value || internship.label}</h1>
          <p>
            {[parsed.company.value, parsed.location.value]
              .filter(Boolean)
              .join(' · ') || 'Company and location were not identified.'}
          </p>
          <div className="internship-detail-actions">
            <Link className="app-secondary-action" to="/resumes">
              Review resumes
            </Link>
            <Link className="app-primary-action" to="/matches">
              Run match analysis
            </Link>
          </div>
        </div>
        <dl>
          <Fact
            confidence={parsed.company.confidence}
            label="Company"
            value={parsed.company.value}
          />
          <Fact
            confidence={parsed.location.confidence}
            label="Location"
            value={parsed.location.value}
          />
          <Fact
            confidence={parsed.experience_level.confidence}
            label="Level"
            value={parsed.experience_level.value}
          />
          <Fact
            label="Application"
            value={internship.application_url ? 'URL available' : null}
          />
        </dl>
      </header>

      <section className="internship-data-overview">
        <article>
          <span className="app-page-eyebrow">Priority distribution</span>
          <h2>Required versus preferred</h2>
          <DataDonut
            data={[
              { name: 'Required', value: requiredTotal, color: '#123b32' },
              { name: 'Preferred', value: preferredTotal, color: '#b7c9c3' },
            ]}
            label="requirements"
            total={requiredTotal + preferredTotal}
          />
        </article>
        <article>
          <span className="app-page-eyebrow">Requirement composition</span>
          <h2>What kind of evidence matters</h2>
          <DataDonut
            data={[
              { name: 'Technical', value: technicalTotal, color: '#123b32' },
              { name: 'Domain', value: domainTotal, color: '#78958c' },
              { name: 'Soft skills', value: softTotal, color: '#d2c7ad' },
            ]}
            label="signals"
            total={technicalTotal + domainTotal + softTotal}
          />
        </article>
      </section>

      <div className="requirement-grid">
        <SkillSection
          label="Required technical"
          skills={parsed.required_skills}
          tone="required"
        />
        <SkillSection
          label="Preferred technical"
          skills={parsed.preferred_skills}
          tone="preferred"
        />
        <SkillSection
          label="Required domain concepts"
          skills={parsed.required_domain_concepts}
          tone="required"
        />
        <SkillSection
          label="Preferred domain concepts"
          skills={parsed.preferred_domain_concepts}
          tone="preferred"
        />
        <SkillSection
          label="Required soft skills"
          skills={parsed.required_soft_skills}
          tone="required"
        />
        <SkillSection
          label="Preferred soft skills"
          skills={parsed.preferred_soft_skills}
          tone="preferred"
        />
      </div>

      <div className="internship-text-columns">
        <TextList
          items={parsed.responsibilities}
          label="Responsibilities"
          title="What the role expects"
        />
        <TextList
          items={parsed.qualifications}
          label="Qualifications"
          title="Candidate signals"
        />
      </div>

      {parsed.review_warnings.length > 0 && (
        <section className="internship-warning-section">
          <span className="app-page-eyebrow">Parser review</span>
          <h2>Ambiguities worth checking</h2>
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

function DetailMessage({
  message,
  title = 'Internship requirements',
}: {
  message: string
  title?: string
}) {
  return (
    <main className="app-page internship-detail-page">
      <Link className="internship-back-link" to="/internships">
        Back to internships
      </Link>
      <div className="internship-detail-message">
        <h1>{title}</h1>
        <p>{message}</p>
      </div>
    </main>
  )
}

function Fact({
  confidence,
  label,
  value,
}: {
  confidence?: number
  label: string
  value: string | null
}) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>
        {value || 'Not found'}
        {confidence !== undefined && (
          <small>{Math.round(confidence * 100)}% confidence</small>
        )}
      </dd>
    </div>
  )
}

function SkillSection({
  label,
  skills,
  tone,
}: {
  label: string
  skills: ExtractedSkill[]
  tone: 'required' | 'preferred'
}) {
  return (
    <section className={`requirement-card is-${tone}`}>
      <header>
        <span>{label}</span>
        <strong>{String(skills.length).padStart(2, '0')}</strong>
      </header>
      {skills.length > 0 ? (
        <div className="requirement-skill-list">
          {skills.map((skill, index) => (
            <article key={`${skill.name}-${index}`}>
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
      ) : (
        <p>None explicitly extracted.</p>
      )}
    </section>
  )
}

function TextList({
  items,
  label,
  title,
}: {
  items: string[]
  label: string
  title: string
}) {
  return (
    <section>
      <span className="app-page-eyebrow">{label}</span>
      <h2>{title}</h2>
      {items.length > 0 ? (
        <ol>
          {items.map((item, index) => (
            <li key={`${item}-${index}`}>
              <span>{String(index + 1).padStart(2, '0')}</span>
              {item}
            </li>
          ))}
        </ol>
      ) : (
        <p className="internship-empty-copy">No items were extracted.</p>
      )}
    </section>
  )
}
