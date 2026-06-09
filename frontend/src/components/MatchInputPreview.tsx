import { Icon } from './Icon'
import { Link } from 'react-router-dom'

export function MatchInputPreview() {
  return (
    <section className="match-entry" aria-label="Match inputs">
      <div className="input-workspace">
        <div className="resume-input">
          <span className="input-icon">
            <Icon name="upload" size={28} />
          </span>
          <h2>Resume input</h2>
          <p>Upload your current resume to establish your baseline skills.</p>
          <button className="button button-outline" type="button">
            Upload resume
          </button>
          <small>
            Or drop your file here
            <strong>PDF and DOCX supported</strong>
          </small>
        </div>

        <div className="internship-input">
          <div className="input-heading">
            <h2>Internship requirements</h2>
            <span>
              <Icon name="document" />
            </span>
          </div>
          <p>
            Paste the target role description to establish the required
            competency matrix.
          </p>
          <label className="visually-hidden" htmlFor="internship-description">
            Internship description
          </label>
          <textarea
            id="internship-description"
            placeholder="Paste the job description here..."
          />
        </div>
      </div>

      <div className="analysis-action">
        <Link
          className="button button-dark button-large"
          state={{ from: { pathname: '/workspace' } }}
          to="/login"
        >
          <Icon name="analysis" />
          Analyze my match
        </Link>
        <p>
          <Icon name="lock" size={13} />
          Your documents remain private to your account and are used only to
          generate your analysis.
        </p>
      </div>
    </section>
  )
}
