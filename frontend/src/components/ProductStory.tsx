import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Icon } from './Icon'
import { fieldStories, type FieldKey } from '../data/careerFields'

export function ProductStory({ selectedField }: { selectedField: FieldKey }) {
  const story = fieldStories[selectedField]
  const [selectedNode, setSelectedNode] = useState(0)
  const [selectedCareer, setSelectedCareer] = useState(0)
  const [selectedStep, setSelectedStep] = useState(0)

  return (
    <div className="product-story story-transition" id="platform" key={selectedField}>
      <section className="story-section profile-story">
        <div className="story-copy">
          <span className="section-index">01 / Profile intelligence</span>
          <h2>Your profile becomes a living evidence map.</h2>
          <p>
            PYXIS extracts skills, projects, certifications, and experience
            from every active resume. Each fact keeps its source, so the system
            knows not only what you claim, but where the evidence came from.
          </p>
          <ul className="feature-points">
            <li>Canonical skills across spelling and naming variations</li>
            <li>Evidence strength from projects, experience, and certificates</li>
            <li>Automatic cleanup when a source resume is removed</li>
          </ul>
        </div>

        <div className="profile-visual" aria-label="Example profile evidence">
          <div className="profile-document">
            <div className="document-topline">
              <span>RESUME / 01</span>
              <span>READY</span>
            </div>
            <h3>{story.profileTitle}</h3>
            <div className="document-lines">
              <span />
              <span />
              <span />
            </div>
            <div className="document-facts">
              <span>16 skills</span>
              <span>4 projects</span>
              <span>2 certifications</span>
            </div>
          </div>

          <div className="evidence-ledger">
            <div className="ledger-heading">
              <span>Profile fact</span>
              <span>Source</span>
              <span>Strength</span>
            </div>
            {story.profileFacts.map(([fact, source, strength]) => (
              <div className="ledger-row" key={fact}>
                <strong>{fact}</strong>
                <span>{source}</span>
                <span>{strength}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="story-section matching-story" id="matching-engine">
        <div className="story-heading centered-story">
          <span className="section-index">02 / Explainable matching</span>
          <h2>A score you can inspect, not simply accept.</h2>
          <p>
            Exact requirements form the deterministic base. Reviewed skill
            relationships add bounded credit, while semantic evidence finds
            supporting passages without silently changing the official score.
          </p>
        </div>

        <div className="matching-visual">
          <div className="score-gauge">
            <div
              className="score-ring"
              style={{
                background: `conic-gradient(var(--primary) 0 ${Math.max(
                  story.score - 12,
                  0,
                )}%, #7e9a91 ${Math.max(
                  story.score - 12,
                  0,
                )}% ${story.score}%, var(--surface-high) ${story.score}% 100%)`,
              }}
            >
              <div>
                <strong>{story.score}</strong>
                <span>match score</span>
              </div>
            </div>
            <div className="score-legend">
              <span title="Canonical requirements matched directly"><i className="exact" />Exact match {Math.max(story.score - 12, 0)}</span>
              <span title="Bounded support from reviewed relationships"><i className="related" />Related evidence 12</span>
              <span title="Requirements that still need evidence"><i className="missing" />Remaining gap {100 - story.score}</span>
            </div>
          </div>

          <div className="coverage-panel">
            <div className="coverage-title">
              <strong>Requirement coverage</strong>
              <span>{story.role}</span>
            </div>
            {story.coverage.map(([label, value]) => (
              <div
                className="coverage-row"
                key={label}
                tabIndex={0}
                title={`${label}: ${value}% covered`}
              >
                <div>
                  <span>{label}</span>
                  <strong>{value}%</strong>
                </div>
                <div className="coverage-track">
                  <span style={{ width: `${value}%` }} />
                </div>
              </div>
            ))}
            <div className="evidence-note">
              <Icon name="check" size={18} />
              <p>
                <strong>{story.evidence.skill}</strong> is supported by{' '}
                {story.evidence.detail}.
              </p>
              <span>{story.evidence.confidence}</span>
            </div>
          </div>
        </div>
      </section>

      <section className="story-section graph-story">
        <div className="graph-visual">
          <div className="graph-caption">
            <span>SKILL RELATIONSHIP GRAPH</span>
            <strong>How existing evidence connects to a target gap</strong>
          </div>
          <div className="skill-graph">
            <svg aria-hidden="true" viewBox="0 0 600 320">
              <path d="M100 95 C220 95 195 160 300 160" />
              <path d="M100 245 C205 245 205 160 300 160" />
              <path d="M300 160 C405 160 395 80 500 80" />
              <path d="M300 160 C415 160 400 240 500 240" />
            </svg>
            {story.graphNodes.map(([skill, state, detail], index) => (
              <button
                aria-pressed={selectedNode === index}
                className={`skill-node node-${index + 1} ${state} ${
                  selectedNode === index ? 'selected' : ''
                }`}
                key={skill}
                onClick={() => setSelectedNode(index)}
                title={detail}
                type="button"
              >
                <span>{skill}</span>
                <small>{state}</small>
              </button>
            ))}
          </div>
          <div className="graph-legend">
            <span><i className="known" />Existing evidence</span>
            <span><i className="related" />Related foundation</span>
            <span><i className="gap" />Target gap</span>
          </div>
          <div className="graph-detail" aria-live="polite">
            <strong>{story.graphNodes[selectedNode][0]}</strong>
            <span>{story.graphNodes[selectedNode][2]}</span>
          </div>
        </div>

        <div className="story-copy">
          <span className="section-index">03 / Skill relationships</span>
          <h2>See the path between what you know and what comes next.</h2>
          <p>
            Neo4j models aliases, related evidence, and prerequisites. That lets
            PYXIS explain why one skill supports another and produce learning
            paths grounded in your current foundation.
          </p>
          <div className="relationship-path">
            <span>{story.relationship[0]}</span>
            <b>supports</b>
            <span>{story.relationship[1]}</span>
            <b>prepares for</b>
            <span>{story.relationship[2]}</span>
          </div>
        </div>
      </section>

      <section className="story-section action-story">
        <div className="story-heading centered-story">
          <span className="section-index">04 / From gaps to action</span>
          <h2>The analysis continues after the score.</h2>
          <p>
            Every gap becomes something usable: a resume correction, a project
            idea, a learning sequence, or a talking point for the interview.
          </p>
        </div>

        <div className="action-board">
          <article className="action-cell improvement-cell">
            <span>RESUME IMPROVEMENT</span>
            <h3>Turn a tool list into evidence.</h3>
            <div className="before-after">
              <div>
                <small>Before</small>
                <p>Listed {story.relationship[0]} and related tools.</p>
              </div>
              <div>
                <small>Suggested framing</small>
                <p>
                  Applied {story.relationship[0]} to produce evidence for{' '}
                  {story.relationship[1]}, with a clear method and outcome.
                </p>
              </div>
            </div>
          </article>

          <article className="action-cell project-cell">
            <span>PROJECT TO BUILD</span>
            <h3>{story.project.title}</h3>
            <p>{story.project.description}</p>
            <div className="tool-list">
              {story.project.tools.map((tool) => <span key={tool}>{tool}</span>)}
            </div>
            <div className="project-outcome">
              <strong>Resume outcome</strong>
              <p>{story.project.outcome}</p>
            </div>
          </article>

          <article className="action-cell roadmap-cell">
            <span>LEARNING SEQUENCE</span>
            {story.learningSequence.map((label, index) => (
              <button
                aria-pressed={selectedStep === index}
                className={`mini-roadmap-step ${
                  selectedStep === index ? 'selected' : ''
                }`}
                key={label}
                onClick={() => setSelectedStep(index)}
                type="button"
              >
                <b>0{index + 1}</b>
                <span>{label}</span>
              </button>
            ))}
            <p className="roadmap-focus">
              Current focus: <strong>{story.learningSequence[selectedStep]}</strong>
            </p>
          </article>
        </div>
      </section>

      <section className="story-section career-story">
        <div className="story-copy">
          <span className="section-index">05 / Career direction</span>
          <h2>Zoom out from one application to your wider direction.</h2>
          <p>
            Profile facts are compared with role requirements in the career
            graph. PYXIS shows realistic paths now, adjacent options worth
            exploring, and the gaps that separate them.
          </p>
          <div className="career-methods">
            <div>
              <strong>Graph fit</strong>
              <span>Deterministic role coverage</span>
            </div>
            <div>
              <strong>AI guidance</strong>
              <span>Projects and practical roadmap</span>
            </div>
          </div>
        </div>

        <div className="career-visual">
          <div className="career-header">
            <span>Recommended directions</span>
            <span>Based on 34 profile facts</span>
          </div>
          {story.careers.map(([path, score, level], index) => (
            <button
              aria-pressed={selectedCareer === index}
              className={`career-row ${
                selectedCareer === index ? 'selected' : ''
              }`}
              key={path}
              onClick={() => setSelectedCareer(index)}
              type="button"
            >
              <span className="career-rank">0{index + 1}</span>
              <div>
                <strong>{path}</strong>
                <span>{level} current fit</span>
              </div>
              <div className="career-bar">
                <span style={{ width: score }} />
              </div>
              <b>{score}</b>
            </button>
          ))}
          <div className="career-gap">
            <span>
              {story.careers[selectedCareer][0]} · highest-impact next skill
            </span>
            <strong>{story.nextSkill}</strong>
            <small>
              Selected fit: {story.careers[selectedCareer][2]} at{' '}
              {story.careers[selectedCareer][1]}
            </small>
          </div>
        </div>
      </section>

      <section className="story-section github-story">
        <div className="github-visual">
          <div className="github-profile-line">
            <div className="github-avatar">AR</div>
            <div>
              <strong>Portfolio evidence</strong>
              <span>12 public repositories analyzed</span>
            </div>
            <b>76 / 100</b>
          </div>
          {story.repositories.map(([repo, stack, result]) => (
            <div className="repo-row" key={repo}>
              <div>
                <strong>{repo}</strong>
                <span>{stack}</span>
              </div>
              <span>{result}</span>
            </div>
          ))}
          <div className="github-match-note">
            <span>MATCH-SPECIFIC EVIDENCE</span>
            <p>
              {story.repositoryEvidence}
            </p>
          </div>
        </div>

        <div className="story-copy">
          <span className="section-index">06 / GitHub portfolio</span>
          <h2>Your repositories become application evidence.</h2>
          <p>
            PYXIS scans public repository metadata, languages, and READMEs. It
            identifies portfolio strengths, presentation problems, resume-ready
            projects, and repositories relevant to a specific internship.
          </p>
          <ul className="feature-points">
            <li>Profile-level portfolio review</li>
            <li>Match-specific repository evidence</li>
            <li>Project questions for interview preparation</li>
          </ul>
        </div>
      </section>

      <section className="story-section interview-story">
        <div className="story-heading centered-story light-copy">
          <span className="section-index">07 / Interview preparation</span>
          <h2>Practice the interview your evidence is likely to create.</h2>
          <p>
            The saved match becomes the interview context: target requirements,
            resume projects, weaker areas, and optional GitHub evidence.
          </p>
        </div>

        <div className="interview-layout">
          <div className="interview-session">
            <div className="session-topbar">
              <span>LIVE PRACTICE / QUESTION 04 OF 10</span>
              <span>Intermediate</span>
            </div>
            <div className="interviewer-message">
              <span>PYXIS</span>
              <p>
                {story.interviewQuestion}
              </p>
            </div>
            <div className="answer-box">
              <span>Your answer</span>
              <p>
                {story.interviewAnswer}
              </p>
            </div>
            <div className="session-footer">
              <span>Evaluation is held until the interview ends.</span>
              <button type="button">Submit answer</button>
            </div>
          </div>

          <div className="interview-summary">
            <span>FINAL FEEDBACK PREVIEW</span>
            <div className="feedback-score">
              <strong>82</strong>
              <span>overall</span>
            </div>
            {story.feedback.map(([label, value]) => (
              <div className="feedback-row" key={label}>
                <span>{label}</span>
                <b>{value}</b>
              </div>
            ))}
            <p>
              Strong project grounding. Improve answer structure and state the
              tradeoffs behind technical decisions.
            </p>
          </div>
        </div>
      </section>

      <section className="closing-story">
        <span className="section-index">Your evidence. Your direction.</span>
        <h2>Move from “Am I qualified?” to “What should I do next?”</h2>
        <p>
          Build your profile, analyze a real internship, understand every gap,
          and prepare to explain your work with confidence.
        </p>
        <Link className="button button-light button-large" to="/signup">
          Start with your resume
        </Link>
      </section>
    </div>
  )
}
