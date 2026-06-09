import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { clearAccessToken, getCachedUser } from '../lib/auth'
import { clearResumeCache } from '../lib/resumes'
import { refreshCurrentUser } from '../lib/session'
import type { User } from '../types/auth'
import './AuthenticatedLayout.css'

const navigation = [
  { to: '/workspace', label: 'Overview', mark: '01' },
  { to: '/resumes', label: 'Resumes', mark: '02' },
  { to: '/internships', label: 'Internships', mark: '03' },
  { to: '/matches', label: 'Match analysis', mark: '04' },
  { to: '/career', label: 'Career direction', mark: '05' },
  { to: '/github', label: 'GitHub portfolio', mark: '06' },
  { to: '/interviews', label: 'Interview prep', mark: '07' },
]

export function AuthenticatedLayout() {
  const navigate = useNavigate()
  const [user, setUser] = useState<User | null>(() => getCachedUser())
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    let active = true
    const validationDelay = user?.id ? 0 : 1200

    const validationTimer = window.setTimeout(() => {
      refreshCurrentUser()
        .then((currentUser) => {
          if (active && currentUser) setUser(currentUser)
        })
        .catch(() => {
          if (active) navigate('/login', { replace: true })
        })
    }, validationDelay)

    return () => {
      active = false
      window.clearTimeout(validationTimer)
    }
  }, [navigate, user?.id])

  function logOut() {
    clearResumeCache()
    clearAccessToken()
    navigate('/', { replace: true })
  }

  return (
    <div className="authenticated-shell">
      <aside className={`app-sidebar ${menuOpen ? 'is-open' : ''}`}>
        <div className="app-sidebar-top">
          <Link className="app-brand" to="/workspace">
            PYXIS
          </Link>
          <button
            aria-label="Close navigation"
            className="app-menu-close"
            onClick={() => setMenuOpen(false)}
            type="button"
          >
            Close
          </button>
        </div>

        <nav className="app-navigation" aria-label="Application">
          {navigation.map((item) => (
            <NavLink
              className={({ isActive }) =>
                `app-nav-link ${isActive ? 'is-active' : ''}`
              }
              key={item.to}
              onClick={() => setMenuOpen(false)}
              to={item.to}
            >
              <span>{item.mark}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="app-sidebar-account">
          <NavLink className="app-profile-link" to="/profile">
            <span className="app-avatar">
              {(user?.full_name || user?.email || 'S').charAt(0).toUpperCase()}
            </span>
            <span>
              <strong>{user?.full_name || 'Student'}</strong>
              <small>{user?.email || 'Checking account...'}</small>
            </span>
          </NavLink>
          <button onClick={logOut} type="button">
            Log out
          </button>
        </div>
      </aside>

      {menuOpen && (
        <button
          aria-label="Close navigation"
          className="app-sidebar-backdrop"
          onClick={() => setMenuOpen(false)}
          type="button"
        />
      )}

      <div className="app-main">
        <header className="app-mobile-header">
          <Link to="/workspace">PYXIS</Link>
          <button onClick={() => setMenuOpen(true)} type="button">
            Menu
          </button>
        </header>
        <Outlet />
      </div>
    </div>
  )
}
