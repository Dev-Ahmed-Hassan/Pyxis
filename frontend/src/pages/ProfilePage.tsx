import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ApiError } from '../lib/api'
import { getCachedUser } from '../lib/auth'
import {
  getCachedProfileFacts,
  getCachedStudentProfile,
  getProfileFacts,
  getStudentProfile,
  refreshProfileFacts,
  updateStudentProfile,
} from '../lib/profile'
import type { User } from '../types/auth'
import type { StudentProfile, UserProfileFacts } from '../types/profile'
import './Profile.css'

export function ProfilePage() {
  const [user] = useState<User | null>(() => getCachedUser())
  const [profile, setProfile] = useState<StudentProfile | null>(
    () => getCachedStudentProfile(),
  )
  const [facts, setFacts] = useState<UserProfileFacts | null>(
    () => getCachedProfileFacts(),
  )
  const [headline, setHeadline] = useState('')
  const [bio, setBio] = useState('')
  const [targetRoles, setTargetRoles] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [refreshingFacts, setRefreshingFacts] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    let active = true

    Promise.allSettled([getStudentProfile(), getProfileFacts()])
      .then(([profileResult, factsResult]) => {
        if (!active) return
        if (profileResult.status === 'fulfilled') {
          applyProfile(profileResult.value)
        }
        if (factsResult.status === 'fulfilled') {
          setFacts(factsResult.value)
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  function applyProfile(nextProfile: StudentProfile) {
    setProfile(nextProfile)
    setHeadline(nextProfile.headline ?? '')
    setBio(nextProfile.bio ?? '')
    setTargetRoles(nextProfile.target_roles.join(', '))
  }

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try {
      setSaving(true)
      setError('')
      setMessage('')
      const updated = await updateStudentProfile({
        headline: headline.trim() || null,
        bio: bio.trim() || null,
        target_roles: parseRoles(targetRoles),
      })
      applyProfile(updated)
      setMessage('Profile updated.')
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setSaving(false)
    }
  }

  async function refreshFacts() {
    try {
      setRefreshingFacts(true)
      setError('')
      setMessage('')
      const refreshed = await refreshProfileFacts()
      setFacts(refreshed)
      setMessage(
        `Profile facts refreshed from ${refreshed.refreshed_resume_count} resume(s).`,
      )
    } catch (requestError) {
      setError(errorMessage(requestError))
    } finally {
      setRefreshingFacts(false)
    }
  }

  const topSkills = useMemo(
    () =>
      [...(facts?.skill_inventory ?? [])]
        .sort((left, right) => right.source_count - left.source_count)
        .slice(0, 24),
    [facts],
  )
  const projects = facts?.project_sources.slice(0, 5) ?? []
  const certifications = facts?.certification_sources.slice(0, 5) ?? []

  return (
    <main className="app-page profile-page">
      <header className="app-page-header profile-hero">
        <div>
          <span className="app-page-eyebrow">Your profile</span>
          <h1>Keep your career evidence organized.</h1>
          <p>
            This profile combines your account details, personal career
            preferences, and facts extracted from your resumes.
          </p>
        </div>
        <button
          className="app-primary-action"
          disabled={refreshingFacts}
          onClick={() => void refreshFacts()}
          type="button"
        >
          {refreshingFacts ? 'Refreshing facts...' : 'Refresh profile facts'}
        </button>
      </header>

      {error && <p className="profile-error">{error}</p>}
      {message && <p className="profile-message">{message}</p>}

      <section className="profile-summary-grid">
        <article>
          <span className="app-page-eyebrow">Account</span>
          <h2>{user?.full_name || 'Student'}</h2>
          <p>{user?.email || 'Signed-in student account'}</p>
          <small>{user?.role || 'student'}</small>
        </article>
        <Metric label="Skills" value={facts?.skill_inventory.length ?? '—'} />
        <Metric label="Projects" value={facts?.project_sources.length ?? '—'} />
        <Metric
          label="Certifications"
          value={facts?.certification_sources.length ?? '—'}
        />
      </section>

      <section className="profile-editor-layout">
        <form onSubmit={saveProfile}>
          <span className="app-page-eyebrow">Career preferences</span>
          <h2>What should PYXIS optimize for?</h2>
          <label>
            Headline
            <input
              maxLength={160}
              onChange={(event) => setHeadline(event.target.value)}
              placeholder="Cybersecurity student focused on web security"
              value={headline}
            />
          </label>
          <label>
            Bio
            <textarea
              maxLength={1000}
              onChange={(event) => setBio(event.target.value)}
              placeholder="A short summary of your interests, goals, and strengths."
              value={bio}
            />
          </label>
          <label>
            Target roles
            <input
              onChange={(event) => setTargetRoles(event.target.value)}
              placeholder="SOC Analyst Intern, Backend Intern"
              value={targetRoles}
            />
          </label>
          <button className="app-primary-action" disabled={saving} type="submit">
            {saving ? 'Saving profile...' : 'Save profile'}
          </button>
        </form>

        <article className="profile-current-card">
          <span className="app-page-eyebrow">Current profile</span>
          <h2>{profile?.headline || 'No headline saved yet'}</h2>
          <p>
            {profile?.bio ||
              'Add a short bio so career recommendations and future interview prep can understand your goals.'}
          </p>
          <div>
            {(profile?.target_roles.length ? profile.target_roles : ['No target roles yet']).map(
              (role) => <small key={role}>{role}</small>,
            )}
          </div>
          <nav className="profile-next-actions" aria-label="Profile next steps">
            <Link className="app-secondary-action" to="/resumes">
              Update resume evidence
            </Link>
            <Link className="app-primary-action" to="/career">
              Get career direction
            </Link>
          </nav>
        </article>
      </section>

      <section className="profile-facts-layout">
        <article className="profile-skills-card">
          <header>
            <span className="app-page-eyebrow">Extracted facts</span>
            <h2>Skill inventory</h2>
          </header>
          {loading ? (
            <p>Loading profile facts...</p>
          ) : topSkills.length ? (
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
              No skills are stored in profile facts yet. Upload a resume, wait
              until it is ready, then refresh facts.
            </p>
          )}
        </article>

        <article>
          <span className="app-page-eyebrow">Project evidence</span>
          <h2>Projects from resumes</h2>
          {projects.length ? (
            projects.map((project) => (
              <section className="profile-fact-row" key={project.id}>
                <strong>{project.project_name || 'Unnamed project'}</strong>
                <p>{project.description[0] || 'No description extracted.'}</p>
                <small>{project.skills.slice(0, 5).join(', ')}</small>
              </section>
            ))
          ) : (
            <p>No project facts extracted yet.</p>
          )}
        </article>

        <article>
          <span className="app-page-eyebrow">Credentials</span>
          <h2>Certifications</h2>
          {certifications.length ? (
            certifications.map((certification) => (
              <section className="profile-fact-row" key={certification.id}>
                <strong>{certification.certification_name}</strong>
                <p>{certification.issuer || 'Issuer not extracted'}</p>
                <small>{certification.date || 'No date'}</small>
              </section>
            ))
          ) : (
            <p>No certifications extracted yet.</p>
          )}
        </article>
      </section>
    </main>
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
    .slice(0, 10)
}

function errorMessage(error: unknown) {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Profile request failed.'
}
