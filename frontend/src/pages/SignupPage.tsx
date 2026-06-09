import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AuthVisual } from '../components/AuthVisual'
import { apiRequest } from '../lib/api'
import type { User } from '../types/auth'
import './Auth.css'

export function SignupPage() {
  const navigate = useNavigate()
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      await apiRequest<User>('/auth/signup', {
        method: 'POST',
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
        }),
      })
      navigate('/login', {
        replace: true,
        state: { notice: 'Account created. Sign in to continue.' },
      })
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Unable to create the account.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-panel">
        <Link className="auth-brand" to="/">PYXIS</Link>
        <div className="auth-form-wrap">
          <span className="auth-eyebrow">Create your profile</span>
          <h1>Start with your evidence.</h1>
          <p className="auth-intro">
            Build a private workspace for resumes, internship matches, learning
            paths, GitHub evidence, and interview preparation.
          </p>

          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="form-field">
              <label htmlFor="signup-name">Full name</label>
              <input
                autoComplete="name"
                id="signup-name"
                minLength={2}
                onChange={(event) => setFullName(event.target.value)}
                required
                value={fullName}
              />
            </div>
            <div className="form-field">
              <label htmlFor="signup-email">Email address</label>
              <input
                autoComplete="email"
                id="signup-email"
                onChange={(event) => setEmail(event.target.value)}
                required
                type="email"
                value={email}
              />
            </div>
            <div className="form-field">
              <label htmlFor="signup-password">Password</label>
              <input
                autoComplete="new-password"
                id="signup-password"
                minLength={8}
                onChange={(event) => setPassword(event.target.value)}
                required
                type="password"
                value={password}
              />
            </div>
            {error && <p className="auth-error" role="alert">{error}</p>}
            <button className="auth-submit" disabled={submitting} type="submit">
              {submitting ? 'Creating account...' : 'Create account'}
            </button>
          </form>

          <p className="auth-switch">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </section>
      <AuthVisual />
    </main>
  )
}
