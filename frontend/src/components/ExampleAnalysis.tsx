import { Icon } from './Icon'
import { fieldStories, type FieldKey } from '../data/careerFields'

function InsightList({
  title,
  items,
  icon,
}: {
  title: string
  items: string[]
  icon: 'check' | 'document' | 'warning'
}) {
  return (
    <section className="insight-block">
      <h3><Icon name={icon} size={18} />{title}</h3>
      <ul>
        {items.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </section>
  )
}

export function ExampleAnalysis({
  selectedField,
  onFieldChange,
}: {
  selectedField: FieldKey
  onFieldChange: (field: FieldKey) => void
}) {
  const example = fieldStories[selectedField]

  return (
    <section className="example-analysis" id="example-analysis">
      <div className="example-heading">
        <div className="section-intro">
          <span className="section-label">Explore the result</span>
          <h2>One profile. Different directions.</h2>
          <p>
            Change the target field and the complete journey below will adapt
            with the analysis.
          </p>
        </div>

        <div className="role-selector" role="tablist" aria-label="Example field">
          {(Object.keys(fieldStories) as FieldKey[]).map((key) => (
            <button
              aria-selected={selectedField === key}
              className={selectedField === key ? 'active' : ''}
              key={key}
              onClick={() => onFieldChange(key)}
              role="tab"
              type="button"
            >
              {fieldStories[key].label}
            </button>
          ))}
        </div>
      </div>

      <div className="selected-role">
        <span>Example target</span>
        <strong>{example.role}</strong>
      </div>

      <div className="analysis-grid analysis-transition" key={selectedField}>
        <div className="analysis-column">
          <section className="score-block">
            <span>Example score</span>
            <strong>{example.score}%</strong>
            <p>{example.summary}</p>
          </section>
          <InsightList icon="check" title="Matched strengths" items={example.strengths} />
        </div>
        <div className="analysis-column">
          <InsightList icon="warning" title="Missing skills" items={example.missingSkills} />
          <InsightList icon="document" title="Resume improvements" items={example.improvements} />
        </div>
        <section className="roadmap-block">
          <h3><Icon name="roadmap" size={18} />Learning roadmap</h3>
          <ol>
            {example.roadmap.map(([title, description]) => (
              <li key={title}><strong>{title}</strong><p>{description}</p></li>
            ))}
          </ol>
        </section>
      </div>
    </section>
  )
}
