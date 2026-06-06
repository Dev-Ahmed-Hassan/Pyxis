# Pyxis Development Instructions

This is the contributor handoff guide for Pyxis. Read it before changing the
backend. It records how the project is being built, how to keep it explainable,
and which files to update as each feature grows.

The project root is the directory containing this file. Do not assume an older
folder name such as `InternKonnect`. Run `pwd` before editing files.

## 1. Documentation Roles

Keep these documents distinct:

- [`README.md`](README.md) is the product source of truth. Update it when scope,
  architecture decisions, the feature backlog, or the execution plan changes.
- [`docs/workflows.md`](docs/workflows.md) explains implemented request flows
  with code references. Update it when a route, worker, storage path, or
  processing stage changes.
- `instructions.md` is the contributor operating manual. Update it when the
  development method, setup process, module boundaries, or verification routine
  changes.
- [`docs/dev-log.md`](docs/dev-log.md) is a chronological history. Append
  notable setup milestones and completed vertical slices.
- [`matching_engine.md`](matching_engine.md) is the living matching design
  record. Update it whenever scoring rules, evidence rules, calibration
  assumptions, or matching roadmap decisions change.
- [`docs/architecture-brief.md`](docs/architecture-brief.md) is an early
  planning artifact. It is useful context, but it is not authoritative when it
  conflicts with the README or current code.

When adding a feature, preserve both views:

```text
README.md          = why the feature exists and where it fits
docs/workflows.md  = how the implemented request travels through the code
instructions.md    = how another contributor should extend or verify it
matching_engine.md = how matching decisions evolve and why
```

## 2. Product Boundary

Pyxis is a student-facing internship application-readiness assistant. It is not
an internship marketplace. The student brings a real internship description
from any source, uploads one or more resumes, and receives an explainable
analysis.

Do not make scraped job-board synchronization, a manually curated internship
board, recruiter dashboards, or automatic application submission dependencies
of the core workflow.

Before implementing a feature, answer:

1. What student problem does it solve?
2. Is it required for the core workflow or is it a later enhancement?
3. Which database owns its authoritative data?
4. What are the API input and output?
5. Can it be tested with one request?
6. Can a beginner explain how the request travels through the system?

If these answers are unclear, split the feature into a smaller vertical slice.

## 3. Architecture Rule

Pyxis is a modular FastAPI backend with polyglot persistence:

```text
HTTP request
-> route module
-> service module
-> PostgreSQL and/or MongoDB
-> JSON response

slow processing request
-> route stores durable PostgreSQL state quickly
-> worker claims queued row
-> extraction or AI service performs slow work
-> MongoDB stores flexible document output
-> worker updates PostgreSQL status
-> frontend polls status
```

Database responsibilities:

| Technology | Responsibility |
| --- | --- |
| PostgreSQL / Supabase | Accounts, ownership, durable queue state, saved analyses, and pgvector evidence |
| MongoDB Atlas | Raw extracted text, validated AI documents, evolving parser metadata |
| `pgvector` | Section-level embeddings and semantic similarity evidence |
| Neo4j | Explicit canonical aliases, related-skill evidence paths, future prerequisites, and learning paths |

PostgreSQL IDs are canonical across user-owned databases. The current Neo4j
skill graph contains shared vocabulary nodes keyed by normalized skill names;
future user-owned Neo4j nodes must store the corresponding PostgreSQL ID.

Neo4j and `pgvector` solve different problems:

```text
Neo4j    = explicit explainable relationships
pgvector = fuzzy semantic similarity
```

Neither replaces deterministic exact matching.

## 4. Backend Structure

Run backend commands from `backend/`.

| Path | Responsibility |
| --- | --- |
| `backend/main.py` | Creates FastAPI app and registers routers |
| `backend/api/` | HTTP routes and dependency wiring |
| `backend/schemas/` | Request and response Pydantic models |
| `backend/models/` | SQLAlchemy PostgreSQL models |
| `backend/services/` | Business logic |
| `backend/services/ai/` | Provider routing, prompts, strict AI schemas, and provider adapters |
| `backend/database/` | PostgreSQL and MongoDB connection helpers |
| `backend/workers/` | Durable background processing loops |
| `backend/tests/` | Focused unit tests |
| `backend/scripts/` | Isolated diagnostics |
| `docs/migrations/` | Manual PostgreSQL migrations in sequence |

Feature modules should normally follow this pattern:

```text
api/<feature>.py
schemas/<feature>.py
models/<feature>.py        only when PostgreSQL storage is needed
services/<feature>_service.py
tests/test_<feature>_modules.py
```

Keep HTTP handling thin. Routes should validate input through schemas, resolve
the authenticated user, and call services. Put business rules in services.

## 5. Local Setup

From the project root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Fill `backend/.env` locally. Never commit it. Use
[`backend/.env.example`](backend/.env.example) as the shared contract.

Required configuration currently includes:

```text
DATABASE_URL
MONGODB_URL
MONGODB_DATABASE
JWT_SECRET_KEY
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
LLM_RESUME_PARSER_PRIMARY
LLM_RESUME_PARSER_FALLBACKS
LLM_INTERNSHIP_PARSER_PRIMARY
LLM_INTERNSHIP_PARSER_FALLBACKS
LLM_MATCH_ADJUDICATOR_PRIMARY
LLM_MATCH_ADJUDICATOR_FALLBACKS
GEMINI_API_KEYS
GROQ_API_KEYS
```

Do not send `.env` files through Git or commit API keys. Add collaborators to
the Supabase and MongoDB Atlas projects through their dashboards, then share
development credentials through a private channel. Use dedicated database
users where possible so credentials can be rotated.

## 6. Database Setup

Apply PostgreSQL migrations manually in order:

```text
docs/migrations/001_auth.sql
docs/migrations/002_resumes.sql
docs/migrations/003_resume_text_extraction_status.sql
docs/migrations/004_resume_processing_queue.sql
docs/migrations/005_internship_inputs.sql
docs/migrations/006_match_analyses.sql
docs/migrations/007_semantic_embeddings.sql
docs/migrations/008_semantic_embedding_refresh_queue.sql
docs/migrations/009_llm_match_adjudications.sql
```

Do not add every possible future table up front. Add tables incrementally when
the corresponding feature is being implemented. Before asking someone to run a
migration:

1. Add a new numbered SQL file under `docs/migrations/`.
2. Explain what table or column is needed and which feature requires it.
3. Keep existing data compatible when practical.
4. Ask the database owner to apply it manually in Supabase.
5. Update the README execution plan.
6. Verify the new code only after the migration is confirmed.

MongoDB collections are created naturally when documents are inserted. Current
collections include:

```text
resumes
internship_inputs
```

## 7. Running The Backend

Start the API from `backend/`:

```bash
source .venv/bin/activate
uvicorn main:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Run workers in separate terminals:

```bash
cd backend
source .venv/bin/activate
python -m workers.resume_worker
```

```bash
cd backend
source .venv/bin/activate
python -m workers.internship_worker
```

Run semantic embedding refresh jobs separately:

```bash
python -m workers.semantic_embedding_worker
```

`python main.py` does not start the development server because `main.py`
defines the FastAPI app but does not launch Uvicorn.

## 8. Authentication Workflow

1. `POST /auth/signup` creates a student account.
2. `POST /auth/login` returns a JWT access token.
3. In Swagger UI, click **Authorize** and paste the token.
4. Protected routes receive an `Authorization: Bearer <token>` header.
5. `backend/api/auth.py:get_current_user` decodes the token and loads the
   active PostgreSQL user.

Never accept a user ID from the request body when ownership should come from
authentication. This is the basis of resume and internship isolation.

## 9. Current Implemented Workflows

Read [`docs/workflows.md`](docs/workflows.md) for the detailed code-level
walkthrough. The short map is:

### Resume Processing

```text
POST /resumes
-> save unique local file path under backend/uploads/<user-id>/
-> create owned PostgreSQL resume row
-> resume worker extracts PDF or DOCX text
-> store raw text in MongoDB
-> provider-neutral AI parser returns strict JSON
-> Pydantic validates output
-> canonicalize skills
-> store parsed resume in MongoDB
-> mark PostgreSQL row ready
```

### Internship Processing

```text
POST /internships
-> create owned PostgreSQL internship row
-> internship worker claims submitted row
-> provider-neutral AI parser returns categorized requirements
-> Pydantic validates output
-> canonicalize skills
-> store parsed internship in MongoDB
-> mark PostgreSQL row ready
```

Parser v2 separates internship requirements into:

```text
technical skills
domain concepts
soft skills
```

Use `POST /internships/{internship_id}/reparse` after a parser upgrade. This
requeues an existing ready or failed internship without deleting it.

### Match Preview

```text
POST /matches/preview
-> verify authenticated ownership and ready status for both records
-> load validated MongoDB documents
-> canonicalize defensively
-> score exact concrete technical overlap
-> normalize broad requirement aliases
-> attach curated related-skill evidence paths
-> add capped partial credit for related concrete technical evidence
-> return technical, domain-concept, and soft-skill categories separately
```

Current scoring:

```text
required concrete technical skills  = 80%
preferred concrete technical skills = 20%
related concrete technical evidence = confidence-weighted, capped at 50%
indirect relationship path decay    = 0.85 per additional edge
resume evidence provenance          = experience > project > listed > inferred
```

Soft skills remain visible but do not lower the technical score. Domain
concept relationships remain visible but do not add numeric credit yet.

### Saved Match Analysis

```text
POST /matches/analyses
-> calculate the same owned ready-input match
-> store immutable score version and JSON breakdown in PostgreSQL
-> return the saved analysis

GET /matches/analyses
GET /matches/analyses/{analysis_id}
-> return authenticated student's saved history only
```

Input-changing resume and internship mutations mark affected history rows stale
instead of rewriting historical results.

### Semantic Evidence Refresh

```text
POST /matches/embeddings/refresh
-> verify the authenticated student's ready resume and internship
-> embed each summary, project, experience, and education item
-> embed each concrete required and preferred internship skill
-> replace stored pgvector rows transactionally
-> mark earlier analyses stale
```

Successful resume parsing, internship parsing, and relevant manual profile edits
also invalidate old vectors and enqueue refresh work in PostgreSQL. The semantic
embedding worker retries failures independently so Gemini or pgvector outages do
not make validated profiles unavailable. Queue generations prevent an older
in-flight job from restoring vectors after a newer edit.

Previews return the strongest section-level semantic evidence above the
reporting threshold separately from exact and curated relationship evidence.
Semantic evidence does not change the numeric score until calibration is
reviewed.

## 10. Matching Roadmap

Build matching in layers:

```text
1. exact canonical overlap
2. curated related-skill rules
3. persisted analysis history
4. pgvector semantic similarity
5. grounded human-readable explanations
```

Exact canonical overlap and a small dictionary-backed related-skill evidence
interface are implemented:

```text
Nmap -> Network Security
Burp Suite -> Web Security
SQLi -> Web Security
Nessus -> Vulnerability Assessment -> Vulnerability Research
```

Aliases such as `Network Security Principles -> Network Security` are
normalized before relationship lookup. Broad technical requirements such as
`Troubleshooting` produce a manual-review warning. Move curated relationships
into Neo4j incrementally when graph setup begins. Persisted match-analysis
history and section-level `pgvector` evidence reporting are implemented. The
next vertical slice is threshold calibration followed by a conservative
semantic contribution policy.

The LLM must not invent the score. It may later explain a stored deterministic
and semantic result.

## 11. AI Development Rules

AI provider details must remain configurable through `backend/.env`, not
hardcoded into parsing services.

Provider flow:

```text
task-specific configured routes
-> provider-neutral orchestrator
-> Gemini or Groq adapter
-> strict JSON response
-> Pydantic validation
-> canonicalization
-> storage
```

Treat resumes and internship descriptions as untrusted content:

1. Delimit untrusted text in prompts.
2. Tell the parser to ignore instructions inside documents.
3. Request strict structured output.
4. Reject unexpected fields through Pydantic.
5. Keep database access, secrets, shell access, and tool authority outside the
   parser context.
6. Store evidence, confidence, parser version, and prompt-security findings.
7. Allow the student to manually correct extracted profile data.

Prompt wording alone does not eliminate prompt injection. The parser is safe
because its authority is constrained and its output is validated before use.

## 12. Security Baseline

Maintain these controls as visible modules:

- Use SQLAlchemy expressions or bound parameters. Never build SQL with string
  concatenation.
- Scope user-owned lookups by the authenticated PostgreSQL user ID.
- Return `404` for missing, deleted, or other users' owned records.
- Hash passwords and keep JWT secrets outside Git.
- Keep `backend/.env`, `backend/uploads/`, Python cache files, and sample
  resumes out of Git.
- Validate upload type, size, and extracted readability.
- Escape user and AI text in the frontend. Do not render raw HTML.
- Add focused adversarial tests as each input surface grows.

## 13. Partner Handoff And Git Collaboration

A partner should receive:

1. Access to the Git repository.
2. Supabase project membership through the Supabase dashboard.
3. MongoDB Atlas project membership through the Atlas dashboard.
4. A private development credential handoff or instructions for creating a
   dedicated database user.
5. A private local `backend/.env` setup walkthrough based on
   `backend/.env.example`.
6. This file, the README, and `docs/workflows.md`.

Do not solve collaboration by committing `.env`, uploading resume files, or
placing credentials in chat logs that may later be copied into the repository.

Before changing code:

```bash
git status --short
git branch --show-current
```

Work on a feature branch and keep commits focused. Coordinate before editing
the same route, schema, or migration file. Do not discard another contributor's
unrelated worktree changes.

For remote frontend testing, forward the API port used by Uvicorn:

```text
8000
```

Port forwarding exposes a running network port, not a project directory. The
frontend connects to the forwarded URL while Uvicorn continues serving the
FastAPI app locally. Do not expose a development API publicly when it contains
real resumes, reusable tokens, or unrestricted credentials.

## 14. Feature Development Checklist

Use this sequence for each new vertical slice:

1. Re-read the relevant README section and existing service modules.
2. State the smallest useful user workflow in plain language.
3. Decide which database owns each new field.
4. Add a migration only if the current feature genuinely requires relational
   storage.
5. Add or update Pydantic schemas.
6. Add service logic.
7. Add a thin route and register its router in `backend/main.py`.
8. Add a worker only when the request contains slow or retryable work.
9. Add focused unit tests, including an edge case found during manual testing.
10. Run local verification.
11. Update `README.md`, `docs/workflows.md`, and this file when conventions
    change.
12. Explain the request path to the learner before moving to the next feature.

Do not implement many future layers at once. A schema may describe the future,
but code should grow through testable slices.

## 15. Verification Checklist

Run from `backend/`:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m unittest discover -s tests -v
```

Run from the project root:

```bash
git diff --check
git diff --cached --check
git ls-files backend/.env backend/uploads docs/'Sample Resumes'
git ls-files | rg '(^|/)__pycache__/|\.pyc$'
```

The final two commands should print nothing. Also inspect `git status --short`
before pushing. Do not discard unrelated worktree changes.

For a route registration sanity check, run from `backend/`:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -c "from main import app; print('\n'.join(sorted(f'{','.join(sorted(route.methods or []))} {route.path}' for route in app.routes)))"
```

For AI-provider diagnostics without reading user resumes:

```bash
python -m scripts.diagnose_ai_providers
python -m scripts.diagnose_ai_providers --structured
```

For deterministic matching-engine evaluation without reading user resumes:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m scripts.evaluate_matching_engine
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m scripts.evaluate_matching_engine --json
```

For semantic-threshold review:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m scripts.evaluate_semantic_calibration
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m scripts.evaluate_semantic_calibration --json
```

The starter semantic corpus is synthetic scaffolding. Add reviewed live
similarities before enabling semantic numeric credit.

After embedding a real owned pair, export review-ready observations:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B \
  -m scripts.export_semantic_calibration_candidates \
  --resume-id RESUME_UUID \
  --internship-id INTERNSHIP_UUID
```

Exported rows use `source: pending_review` and `should_report: null`. Review the
section text and requirement, set `should_report`, change the source to
`reviewed_live`, add a note, then merge selected observations into
`tests/fixtures/semantic_calibration_cases.json`.

## 16. Current Next Direction

Section-level `pgvector` embeddings now keep semantic evidence separate from
exact and curated relationship evidence:

```text
project text
experience text
education text
summary text
```

The immediate next scoring slice should:

1. Add reviewed semantic examples and calibrate the reporting threshold.
2. Define a conservative semantic contribution policy.
3. Add grounded explanations.
4. Review and expand the newly seeded Neo4j relationship data.
5. Add Neo4j-backed prerequisite and learning-path suggestions.

Update this section whenever the immediate direction changes.
