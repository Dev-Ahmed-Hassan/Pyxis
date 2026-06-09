# Pyxis

Pyxis is an AI-assisted career navigation backend for students. It converts a
student resume and an internship description into validated structured data so
the next phase can calculate explainable matches, identify skill gaps, and
suggest a practical improvement roadmap.

Developer handoff and local setup instructions are in
[docs/development-setup.md](docs/development-setup.md).

Current API behavior and frontend workflow are documented in
[docs/api-workings.md](docs/api-workings.md). The implementation contract for
the planned interview feature is in
[docs/interview-module-handoff.md](docs/interview-module-handoff.md).
Frontend implementation coverage is tracked in
[docs/frontend-feature-coverage.md](docs/frontend-feature-coverage.md).

## Current Backend

The current FastAPI backend supports JWT authentication, student profiles,
owned resume uploads, asynchronous PDF and DOCX extraction, AI resume parsing,
manual resume-profile corrections, skill canonicalization, and asynchronous
internship-description parsing.

The backend intentionally uses a polyglot architecture:

- PostgreSQL stores accounts, ownership, operational state, and durable worker
  queues.
- MongoDB stores raw extracted text and evolving validated AI documents.
- Neo4j stores explicit skill relationships and supports future prerequisite
  and roadmap suggestions during explainable matching.
- `pgvector` stores section-level semantic evidence for matching.

## Processing Model

Uploads and internship submissions return quickly. Separate workers claim
durable PostgreSQL queue rows, perform slower extraction and AI work, store
documents in MongoDB, and update statuses for frontend polling. Temporary
provider or storage failures can be retried without asking the student to
resubmit data.

The detailed code-level walkthrough is in
[`docs/workflows.md`](docs/workflows.md).

Contributors should read [`instructions.md`](instructions.md) before changing
the backend. It records setup, module boundaries, migration rules, verification
commands, and the current handoff direction.

The matching strategy, scoring decisions, known weaknesses, and improvement
plan live in [`matching_engine.md`](matching_engine.md). Update it alongside
every matching-engine revision.

## Current Internship Endpoints

- `POST /internships`
- `GET /internships`
- `GET /internships/{internship_id}`
- `GET /internships/{internship_id}/parsed-requirements`
- `POST /internships/{internship_id}/retry`
- `POST /internships/{internship_id}/reparse`
- `DELETE /internships/{internship_id}`

## Current Profile Endpoints

- `GET /profile`
- `PATCH /profile`
- `GET /profile/facts`
- `POST /profile/facts/refresh`

`POST /profile/facts/refresh` rebuilds a profile-level skill, project, and
certification inventory from all active ready parsed resumes. Each extracted
fact keeps its source `resume_id`, source section, confidence, and evidence so
the system can remove facts from one resume without losing facts from other
resumes. Successful resume parsing and manual parsed-profile edits replace the
facts for that one resume automatically; deleting a resume removes that
resume's profile facts.

## Current Career Endpoints

- `POST /career/recommendations`
- `GET /career/recommendations/{recommendation_id}`

Career recommendations are profile-level, not internship-match-specific. The
service uses profile facts extracted from saved resumes, retrieves career
guidance chunks from the RAG knowledge index, generates structured path
recommendations, and saves the result for later reuse.

## Current GitHub Endpoints

- `POST /github/snapshots`
- `GET /github/snapshots/latest`
- `GET /github/snapshots/latest/compact`
- `GET /github/snapshots/{snapshot_id}`
- `GET /github/snapshots/{snapshot_id}/compact`
- `POST /github/analyses`
- `GET /github/analyses/latest`
- `GET /github/analyses/{analysis_id}`

GitHub snapshots are optional profile enrichment. Snapshot creation fetches and
stores raw public GitHub API responses: profile payload, repositories,
per-repository languages, and README API payloads. The saved analysis layer then
interprets the compact snapshot for UI use.

Compact GitHub snapshots are also stored and exposed for frontend and future
LLM use. They summarize profile fields, repository metadata, language totals,
README availability, and decoded README excerpts so UI and AI analysis do not
need the full raw GitHub API payload.

GitHub analyses are the UI-facing portfolio interpretation layer. The service
uses the compact snapshot, not the raw GitHub payload, and saves a structured
analysis with portfolio score, technology summary, strong repositories,
resume-worthy projects, weak repositories, README improvements, career
alignment, and recommended actions. Re-running analysis for the same snapshot
and same request returns the saved result unless `force_refresh` is true.

GitHub analysis has two product meanings and they should not be mixed:

```text
1. Profile-level GitHub portfolio analysis
   Input: compact GitHub snapshot + selected target field / preferred roles
   Output: general portfolio strength, strong repos, weak repos, README fixes,
   career alignment, and portfolio improvement actions
   Storage: /github/analyses

2. Match-specific GitHub evidence, planned later
   Input: saved resume/internship match + compact GitHub snapshot
   Output: repositories that support this exact internship, repos to mention in
   applications, project evidence for missing/matched requirements
   Storage: separate future match-specific table, not /github/analyses
```

Interview preparation should use concrete saved evidence first: parsed resume
profile, parsed internship requirements, saved match analysis, saved match
explanation, and compact GitHub repository data if available. The profile-level
GitHub LLM analysis can be shown as background portfolio advice, but interview
questions should not depend on it because it is not tied to one specific resume
and internship pair.

## Current Matching Endpoint

- `POST /matches/preview`
- `POST /matches/embeddings/refresh`
- `POST /matches/analyses`
- `GET /matches/analyses`
- `GET /matches/analyses/{analysis_id}`
- `POST /matches/adjudications`
- `GET /matches/adjudications/{adjudication_id}`
- `POST /matches/explainability/knowledge/embeddings/refresh`
- `POST /matches/explainability/knowledge/search`
- `POST /matches/explanations`
- `GET /matches/explanations/{explanation_id}`
- `POST /matches/github-evidence`
- `GET /matches/github-evidence/latest?match_analysis_id=...`
- `GET /matches/github-evidence/{evidence_id}`

This first matching route calculates an on-demand canonical skill-overlap
preview. It verifies that the ready resume and ready internship input belong to
the authenticated student, then reports matched skills, missing required
skills, missing preferred skills, applied weights, curated related-skill
evidence, an exact-overlap subtotal, capped related-skill credit, and warnings.
The preview route does not persist analysis history.

`POST /matches/analyses` runs the same calculation and persists an immutable,
versioned PostgreSQL history row. Saved analyses retain their full JSON evidence
breakdown and are marked stale when their resume or internship input changes.

`POST /matches/adjudications` reviews missing concrete requirements with
retrieved resume evidence and stores a bounded AI-reviewed shadow comparison.
`POST /matches/explanations` uses a saved analysis, optional saved
adjudication, and retrieved match-explainability knowledge chunks to generate a
student-facing gap analyzer response.

`POST /matches/github-evidence` uses a saved match analysis and the latest or
selected compact GitHub snapshot to generate match-specific repository evidence.
This is separate from profile-level `/github/analyses`: it answers which repos
support this exact internship match, which requirements GitHub can or cannot
support, which projects to mention in applications, and which project-specific
interview questions to practice.

## Planned GUI Visuals

The backend returns structured data so the frontend can present matching as a
clear product experience rather than raw JSON. Planned visual surfaces include:

```text
1. Match Score Ring
   Show base score and AI-reviewed score side by side.

2. AI Adjustment Indicator
   Show evidence-backed adjustment points with the configured cap.

3. Requirement Coverage Bars
   Show required and preferred technical coverage percentages.

4. Skill Breakdown Chart
   Group requirements into matched, partial, and missing.

5. Gap Severity Chart
   Group missing requirements by high, medium, and low severity.

6. Strength Cards
   Show strongest matched requirements with evidence section chips.

7. Partial Match Cards
   Explain related or adjudicated support without overstating it.

8. Resume Improvement Checklist
   Convert resume_improvements into actionable UI tasks.

9. Suggested Project Cards
   Render learning_projects with goal, tools, steps, and resume outcome.

10. Interview Prep Cards
    Render interview_talking_points as practice questions tied to evidence.

11. Fairness / Underestimation Note
    Explain when the base score may be conservative because evidence appears in
    projects or adjacent wording rather than exact skill names.

12. Analysis History
    Show saved analyses over time and mark stale results when inputs change.
```

The explanation payload is intentionally UI-shaped:

```text
score_card
strengths
partial_matches
gaps
resume_improvements
learning_projects
interview_talking_points
fairness_notes
```

If a frontend screen needs a different shape, prefer adding a stable
frontend-friendly field to the API over forcing the UI to infer meaning from
raw internal evidence.

## Planned Product Modules

These modules should feel connected in the GUI rather than appearing as
separate backend tools.

### Interview Preparation

Interview preparation is match-specific. It should start from a saved analysis
dashboard after the student has matched one resume to one internship.

Mode 1: Prepared Question Set

```text
saved analysis + saved explanation
-> technical questions
-> project deep-dive questions
-> gap-focused practice questions
-> behavioral questions
-> closing pitch prompt
```

This is the MVP interview feature because it is easy to display and reuse.

Mode 2: Interactive Mock Interview

```text
saved analysis + saved explanation
-> ask one question
-> student answers
-> AI evaluates answer
-> AI asks follow-up
-> final feedback report
```

This is a later interactive layer. It should use the prepared question set as
the foundation rather than starting from scratch.

### GitHub Profile Review

GitHub review is planned as a profile-enrichment module. It should inspect a
student's public repositories and extract portfolio evidence such as:

```text
languages
frameworks
project topics
README quality
security or AI project signals
commit/activity indicators
repository presentation issues
possible resume-project evidence
```

The review should not replace resume parsing. It should add another evidence
source that can support:

```text
profile facts
career recommendations
match explanations
resume improvement suggestions
interview project deep dives
```

Product boundary:

```text
Profile-level GitHub review
-> general portfolio advice for a selected field

Match-specific GitHub evidence
-> optional future section inside one resume-to-internship dashboard

Interview prep
-> uses concrete parsed/saved evidence and compact repo facts, with GitHub LLM
   analysis only as optional background
```

Potential GUI surface:

```text
Profile Dashboard
-> Resume Facts
-> GitHub Portfolio Review
-> Career Paths
-> Suggested Projects
```

### Connected UI Journey

The UI should be organized around student goals, not backend endpoints:

```text
1. Profile Hub
   resumes, parsed facts, GitHub portfolio, skill inventory, certifications

2. Career Direction
   profile-level career recommendations and learning roadmap

3. Internship Match Dashboard
   selected resume + internship, score, gaps, improvements, project advice

4. Interview Prep
   generated from a saved match dashboard

5. Application Workspace
   selected resume, notes, prep checklist, and status tracking
```

Backend APIs may remain modular, but the frontend should present them as one
workflow:

```text
Who am I?
Where should I go?
How well do I fit this internship?
How do I improve?
How do I prepare?
```

## Database Migration

The internship queue table and match-analysis history table are defined in
[`docs/migrations/005_internship_inputs.sql`](docs/migrations/005_internship_inputs.sql)
and [`docs/migrations/006_match_analyses.sql`](docs/migrations/006_match_analyses.sql).
Semantic embedding tables are defined in
[`docs/migrations/007_semantic_embeddings.sql`](docs/migrations/007_semantic_embeddings.sql).
The durable asynchronous refresh queue is defined in
[`docs/migrations/008_semantic_embedding_refresh_queue.sql`](docs/migrations/008_semantic_embedding_refresh_queue.sql).
Shadow LLM evidence audits are defined in
[`docs/migrations/009_llm_match_adjudications.sql`](docs/migrations/009_llm_match_adjudications.sql).
RAG match-explainability knowledge chunks are defined in
[`docs/migrations/010_match_explainability_knowledge.sql`](docs/migrations/010_match_explainability_knowledge.sql).
Knowledge authoring format and current source files live in
[`backend/knowledge/match_explainability/README.md`](backend/knowledge/match_explainability/README.md).
Saved match explanations are defined in
[`docs/migrations/011_match_explanations.sql`](docs/migrations/011_match_explanations.sql).
Profile-level resume facts are defined in
[`docs/migrations/012_user_profile_resume_facts.sql`](docs/migrations/012_user_profile_resume_facts.sql).
Profile-level career recommendations are defined in
[`docs/migrations/013_career_recommendations.sql`](docs/migrations/013_career_recommendations.sql).
Raw GitHub profile snapshots are defined in
[`docs/migrations/014_github_profile_snapshots.sql`](docs/migrations/014_github_profile_snapshots.sql).
Compact GitHub snapshot storage is added in
[`docs/migrations/015_github_compact_snapshots.sql`](docs/migrations/015_github_compact_snapshots.sql).
Saved GitHub portfolio analyses are defined in
[`docs/migrations/016_github_profile_analyses.sql`](docs/migrations/016_github_profile_analyses.sql).
Saved match-specific GitHub evidence is defined in
[`docs/migrations/017_github_match_evidence.sql`](docs/migrations/017_github_match_evidence.sql).
Apply migrations manually in sequence when preparing a fresh PostgreSQL
database.

## Immediate Next Phase

The next scoring step is reviewing stored shadow LLM adjudications alongside
human labels, calibrating semantic retrieval, and deciding whether any bounded
adjudicated credit is reliable enough to graduate into the official score.
Neo4j-backed gap suggestions remain incremental.

## Product Boundary

Pyxis is an application-readiness assistant, not an internship marketplace. A
student brings a real internship description from any source. Pyxis helps them
answer:

```text
Is my resume suitable for this internship?
Which version of my resume should I use?
What important skills am I missing?
How can I improve before applying?
What should I prepare for the interview?
```

The MVP does not depend on scraping or synchronizing job boards. External
discovery platforms can later integrate the matching capability through an API,
but that is an expansion rather than a dependency.

## Core Workflow

```text
student creates an account
-> student uploads one or more resumes
-> system extracts and structures resume content
-> student pastes a real internship description and optional source link
-> system extracts internship requirements
-> system compares selected resumes with those requirements
-> student receives scores, explanations, skill gaps, and suggestions
-> student selects the strongest resume and tracks application progress
-> student generates targeted interview preparation
```

## Resume Processing Blueprint

```text
Upload PDF or DOCX
-> validate MIME type, file size, and readability
-> extract text with PyMuPDF or python-docx
-> clean formatting noise
-> call the configured LLM with a schema-guided prompt
-> validate parsed JSON with Pydantic
-> calculate per-field confidence indicators
-> separate certifications from skills
-> distinguish explicit skills from cautious evidence-backed inferences
-> canonicalize aliases such as "js" -> "JavaScript"
-> store raw text, parsed JSON, and parser metadata in MongoDB
-> generate section-level embeddings through the owned refresh endpoint
-> store embeddings with pgvector
-> mark the profile ready
```

Confidence is a review indicator, not proof that an extraction is correct.
Low-confidence and inferred fields should be visible to the student for manual
confirmation.

## Matching Design

The LLM must not invent the final match score. Pyxis calculates official scores
from canonical structured data and reviewed relationships. The optional
`POST /matches/adjudications` shadow path asks an LLM to classify missed
evidence with strict resume-passage citations; Python computes a bounded shadow
comparison while leaving the official score unchanged.

`POST /matches/embeddings/refresh` generates auditable resume-section and
internship-requirement embeddings for one owned ready-input pair. Match previews
report semantic evidence separately. It does not affect the numeric score until
its threshold and contribution policy have been calibrated.

Successful parser runs and relevant profile edits also invalidate old vectors
and queue asynchronous regeneration. Run `python -m workers.semantic_embedding_worker`
from `backend/` to process retryable refresh jobs.

Use `python -m scripts.export_semantic_calibration_candidates --resume-id ... --internship-id ...`
to export stored live comparisons as unlabeled `pending_review` observations.

Initial baseline weights:

| Section | Weight |
| --- | ---: |
| Skills similarity | 40% |
| Projects similarity | 30% |
| Experience similarity | 20% |
| Education similarity | 10% |

These weights are evaluation baselines, not permanent assumptions. When
embeddings are unavailable or input data is sparse, fall back to canonical
skill overlap and structured rules. Scores below `30%` should be labelled weak
matches rather than inflated to avoid an empty state.

Internship requirements must be separated into three categories:

```text
technical skills = concrete tools, platforms, languages, and teachable abilities
domain concepts  = broader knowledge areas such as web or network security
soft skills      = communication, teamwork, attention to detail, and work habits
```

Soft skills remain visible to the student but must not dominate the technical
match score. Broad domain concepts also remain visible, but exact-name matching
alone is not sufficient evidence for scoring them.

Matching grows through three complementary layers:

```text
1. exact canonical overlap
   "js" -> "JavaScript"

2. curated related-skill rules
   Nmap -> evidence of Network Security
   SQLi -> evidence of Web Security
   Nessus -> Vulnerability Assessment -> evidence of Vulnerability Research

3. pgvector semantic similarity
   project and experience text -> broader evidence for a requirement
```

Exact canonical overlap is the deterministic baseline and must continue to work
when richer services are unavailable. Neo4j becomes the long-term home for
explicit related-skill and prerequisite relationships. `pgvector` complements
the graph by recognizing fuzzier semantic similarity in resume sections.

Curated evidence for a missing concrete technical requirement receives
confidence-weighted partial credit capped at `50%` of that requirement's normal
value. Indirect paths decay by distance, and the strongest reviewed path
determines credit without hiding alternative evidence. Domain-concept evidence
remains visible but does not add numeric credit yet. The response keeps the
exact-overlap subtotal and related-skill contribution separate.

Resume evidence also preserves provenance. Related evidence demonstrated in
experience or projects carries more weight than a bare skills-list mention or
cautious parser inference. Exact canonical matches remain deterministic while
returning their strongest evidence for explanation.

Each analysis should store at least:

```text
resume_id
internship_input_id
analysis_session_id
score_version
overall_score
section_scores
created_at
stale_at = optional
```

The output should include matched skills, missing required skills, missing
preferred skills, relevant evidence, a score breakdown, and an input-quality
warning when needed.

## Neo4j Skill Graph

The first Neo4j graph slice is implemented. Domain JSON datasets are the
authoring source for canonical skills, aliases, and relationships:

```text
backend/data/skill_graph/
├── ai_ml.json
├── cloud_engineering.json
├── common_skills.json
├── cybersecurity.json
├── software_engineering.json
└── web_development.json
```

The seed command validates and mirrors those datasets into:

```text
(SkillTerm)-[:ALIAS_OF]->(Skill)
(Skill)-[:EVIDENCE_FOR]->(Skill)
(Skill)-[:RELATED_TO]->(Skill)
(Skill)-[:PREREQUISITE_FOR]->(Skill)
```

Run the idempotent seed from `backend/`:

```bash
.venv/bin/python -m scripts.seed_neo4j_skill_graph
```

Live match previews query Neo4j for short explainable support paths. If Neo4j
is unconfigured, unavailable, or has no matching path, the matcher falls back
to the local curated provider. Exact canonical matching remains deterministic
and independent of Neo4j.

Validate after editing:

```bash
.venv/bin/python -m scripts.validate_skill_graph_data
```

Then rerun the Neo4j seed. See `docs/neo4j-skill-graph.md` for the exact JSON
format and extension workflow.

## Security Modules

Security stays visible while core functionality grows:

- Authorization scopes every resume, internship input, and analysis lookup to
  the authenticated PostgreSQL user ID.
- SQLAlchemy expressions and bound parameters prevent SQL injection. Future raw
  SQL must never use string concatenation.
- Frontend text rendering must escape profile text, aliases, AI output, and RAG
  answers to prevent stored XSS.
- Resume text and internship descriptions are untrusted LLM input. Prompts
  delimit them clearly, schemas reject unexpected fields, and parser output
  never receives SQL, HTML, shell, database, or tool authority.
- Upload rules allow PDF and DOCX only, reject empty files, enforce the size
  limit, and keep expensive processing in durable workers.

Prompt wording cannot eliminate prompt injection. The important protection is
that parsing is constrained, validated, evidence-carrying, and separated from
privileged actions.

## Feature Backlog

Current and planned student-facing capabilities:

- multiple resume slots with aliases and one default resume
- editable validated resume profiles with confidence indicators
- pasted internship descriptions with optional source URLs
- explainable resume-to-internship scoring
- comparison of several resumes for one internship
- grouped skill gaps and truthful resume-improvement suggestions
- bookmarks and external application tracking
- text-based targeted mock interviews
- optional voice interviews using speech-to-text and text-to-speech
- optional RAG career guidance over curated documents with citations
- optional GitHub portfolio review through the public GitHub API
- optional LinkedIn feedback from pasted profile text only

## Execution Plan

### Completed Foundation

- [x] configure FastAPI, PostgreSQL / Supabase, MongoDB Atlas, and health routes
- [x] implement signup, password hashing, login, JWT validation, and profiles
- [x] implement owned resume upload, extraction, durable retries, AI parsing,
  manual corrections, and confidence indicators
- [x] add dictionary-backed skill canonicalization for parsed and manually
  corrected resume skills
- [x] accept internship descriptions and parse canonical requirements through a
  separate durable worker

### Next: Basic Matching

- [x] create PostgreSQL analysis tables incrementally
- [x] calculate rule-based required and preferred skill overlap
- [x] return an explainable first match response
- [x] separate technical skills, domain concepts, and soft skills in parsing and
  preview output
- [x] add a dictionary-backed related-skill evidence interface
- [x] add capped partial credit for related concrete technical evidence
- [x] add typed relationships, confidence weights, and path-distance decay
- [x] preserve resume evidence provenance and weight related evidence quality
- [x] mirror canonical aliases and curated related-skill rules into Neo4j
- [x] use Neo4j support paths in live matching with a local fallback
- [x] generate section-level embeddings and store them with pgvector
- [x] report semantic evidence separately without silently changing the score
- [x] invalidate stale vectors and refresh them through a durable retry queue
- [x] add an offline semantic-threshold calibration report
- [x] export stored live similarities into review-ready calibration observations
- [ ] calibrate semantic reporting thresholds against reviewed examples
- [ ] combine structured and semantic scores
- [x] persist versioned analysis history and mark changed inputs stale

### Later: Student Workflow And Graph Enrichment

- [ ] compare multiple resumes for one internship
- [ ] add bookmarks and external application tracking
- [ ] generate text-based interview preparation
- [x] configure Neo4j and load the curated skill graph
- [x] return match-specific prerequisite learning paths
- [x] add profile-level role fit and career gap recommendations
- [ ] connect learning gaps to reviewed learning resources

## Decision Ledger

Retained from earlier broad proposals: field confidence, manual corrections,
processing states, fallback scoring, section-level embeddings, explainable
breakdowns, skill canonicalization, validated LLM output, security modules, RAG
guidance, and interview preparation.

Deferred until the core workflow works: Neo4j learning paths, GitHub review,
voice interviews, LinkedIn feedback from pasted text, and broader dashboards.

Rejected as core dependencies: scraping-only opportunity discovery, automatic
job-board synchronization, presenting a manually curated internship list as a
complete discovery product, scraped LinkedIn ingestion, and scraped community
content as the first RAG knowledge base.

## Working Rule

Before adding a feature, answer:

- What student problem does it solve?
- Is it required for the core workflow?
- Which database owns its data?
- What is the API input and output?
- How can it be tested with one request?
