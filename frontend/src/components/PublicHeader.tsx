import { Link } from 'react-router-dom'

export function PublicHeader() {
  return (
    <header className="public-header">
      <div className="header-inner">
        <Link className="wordmark" to="/" aria-label="PYXIS home">
          PYXIS
        </Link>

        <nav className="public-nav" aria-label="Public navigation">
          <a href="#how-it-works">How it works</a>
          <a href="#matching-engine">Matching</a>
          <a href="#platform">Platform</a>
        </nav>

        <div className="header-actions">
          <Link className="text-link" to="/login">
            Log in
          </Link>
          <Link className="button button-dark button-small" to="/signup">
            Get started
          </Link>
        </div>
      </div>
    </header>
  )
}
