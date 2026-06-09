export function AuthVisual() {
  return (
    <aside className="auth-visual" aria-label="PYXIS product preview">
      <div className="auth-visual-inner">
        <div className="auth-visual-copy">
          <span>Evidence before advice</span>
          <h2>Build career decisions from work you can actually explain.</h2>
        </div>

        <div className="auth-evidence-preview">
          <div className="auth-preview-header">
            <span>Profile evidence</span>
            <span>Source</span>
            <span>Strength</span>
          </div>
          {[
            ['Python', '3 projects', 'Strong'],
            ['Network analysis', 'Project 02', 'Strong'],
            ['Technical reporting', 'Experience', 'Moderate'],
            ['Incident response', 'Coursework', 'Emerging'],
          ].map(([fact, source, strength]) => (
            <div className="auth-preview-row" key={fact}>
              <strong>{fact}</strong>
              <span>{source}</span>
              <span>{strength}</span>
            </div>
          ))}
        </div>
      </div>
    </aside>
  )
}
