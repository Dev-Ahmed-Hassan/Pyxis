import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { AuthVisual } from '../components/AuthVisual'
import { apiRequest } from '../lib/api'
import { cacheProvisionalUser, setAccessToken } from '../lib/auth'
import type { TokenResponse } from '../types/auth'
import './Auth.css'

type LocationState = {
  from?: { pathname?: string }
  notice?: string
}

export function LoginPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as LocationState | null
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const token = await apiRequest<TokenResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      })
      setAccessToken(token.access_token)
      cacheProvisionalUser(email)
      navigate(state?.from?.pathname || '/workspace', { replace: true })
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : 'Unable to log in.',
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
          <span className="auth-eyebrow">Welcome back</span>
          <h1>Continue your workspace.</h1>
          <p className="auth-intro">
            Sign in to access saved resumes, analyses, career guidance, and
            interview preparation.
          </p>

          {state?.notice && <p className="auth-notice">{state.notice}</p>}

          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="form-field">
              <label htmlFor="login-email">Email address</label>
              <input
                autoComplete="email"
                id="login-email"
                onChange={(event) => setEmail(event.target.value)}
                required
                type="email"
                value={email}
              />
            </div>
            <div className="form-field">
              <label htmlFor="login-password">Password</label>
              <input
                autoComplete="current-password"
                id="login-password"
                minLength={8}
                onChange={(event) => setPassword(event.target.value)}
                required
                type="password"
                value={password}
              />
            </div>
            {error && <p className="auth-error" role="alert">{error}</p>}
            <button className="auth-submit" disabled={submitting} type="submit">
              {submitting ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <p className="auth-switch">
            New to PYXIS? <Link to="/signup">Create an account</Link>
          </p>
        </div>
      </section>
      <AuthVisual />
    </main>
  )
}
