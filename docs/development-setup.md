# Development Setup

This guide is for a teammate setting up the PYXIS backend on a new machine.
Complete the sections in order. Commands are run from the repository root
unless the guide says otherwise.

## 1. What Is Shared

Git contains the source code, tests, migrations, curated knowledge documents,
skill-graph data, `.env.example`, and documentation.

Git does not contain the real `.env`, uploaded resumes, virtual environments,
caches, or logs. A teammate must create a local `backend/.env`.

## 2. Prerequisites

Install:

- Git
- Python 3.14 to match the current development environment
- access to the shared PostgreSQL, MongoDB Atlas, and Neo4j databases
- at least one configured AI provider key

The databases are hosted services, so the teammate does not need to install
PostgreSQL, MongoDB, or Neo4j locally when using the shared development setup.

## 3. Clone And Install

### Windows PowerShell

```powershell
git clone <repository-url>
cd PYXIS\backend
py -3.14 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

If `py -3.14` is unavailable, check installed versions with `py --list`.

### Linux Or macOS

```bash
git clone <repository-url>
cd PYXIS/backend
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

## 4. Configure `.env`

The project owner should transmit development credentials privately. Do not
send `.env` through Git or commit it.

Required groups:

| Configuration | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL, pgvector, queues, users, saved analyses |
| `MONGODB_URL`, `MONGODB_DATABASE` | Extracted and parsed resume/internship documents |
| `JWT_SECRET_KEY`, `JWT_ALGORITHM` | Login access tokens |
| `GEMINI_API_KEYS`, `GROQ_API_KEYS` | AI parsing and analysis providers |
| `LLM_*_PRIMARY`, `LLM_*_FALLBACKS` | Provider route for each AI task |
| `EMBEDDING_MODEL_ROUTE`, `EMBEDDING_DIMENSIONS` | Semantic and knowledge embeddings |
| `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` | Skill and career graph |
| `GITHUB_API_TOKEN` | Optional higher GitHub public API rate limit |

The teammate may initially use the same development database credentials.
Prefer separate restricted database users where the providers support them.
Use only test resumes and internship descriptions in shared development data.

## 5. Database Preparation

PostgreSQL migrations are in `docs/migrations/` and currently run from `001`
through `017`.

For an existing shared database, do not rerun migrations. Ask the project owner
whether all migrations are already applied.

For a new empty database, apply every SQL migration in numerical order through
the provider SQL editor or another PostgreSQL client.

Neo4j data is generated from `backend/data/skill_graph/`. From `backend/`:

```bash
python -m scripts.validate_skill_graph_data
python -m scripts.seed_neo4j_skill_graph
```

Rerun both after reviewed skill-graph data changes. Seeding uses merge
operations and is intended to be repeatable.

## 6. Verify Connections

From `backend/`, start the API:

```bash
uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/health
http://127.0.0.1:8000/health/postgres
http://127.0.0.1:8000/health/mongo
http://127.0.0.1:8000/health/neo4j
```

All three database health checks should report a connection. A healthy API
alone does not prove that the external databases are reachable.

## 7. Start Background Workers

Keep the API running and open separate terminals in `backend/`. Activate the
virtual environment in each terminal.

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
python -m workers.resume_worker
```

Linux or macOS:

```bash
source .venv/bin/activate
python -m workers.resume_worker
```

Repeat for:

```bash
python -m workers.internship_worker
python -m workers.semantic_embedding_worker
```

Worker responsibilities:

- `resume_worker`: text extraction, AI parsing, canonicalization, profile facts
  synchronization, and semantic refresh queuing.
- `internship_worker`: AI requirement parsing, canonicalization, and semantic
  refresh queuing.
- `semantic_embedding_worker`: asynchronous resume and internship embeddings.

Knowledge-document embedding refresh is performed directly by its API endpoint
and does not require the semantic worker.

## 8. First Smoke Test

1. Create or log in to a test account.
2. Authorize Swagger with `Bearer <access_token>`.
3. Upload one resume while `resume_worker` is running.
4. Create one internship while `internship_worker` is running.
5. Poll each record until `processing_status` is `ready`.
6. Call `POST /matches/preview`.

See [api-workings.md](api-workings.md) for complete workflows.

## 9. Team Git Workflow

The teammate should create a branch from the agreed shared baseline:

```bash
git switch <shared-baseline-branch>
git pull
git switch -c feature/interview-prep
git push -u origin feature/interview-prep
```

Rules:

- Commit only interview-module files and explicitly coordinated shared files.
- Never commit `.env`, uploads, generated caches, or test credentials.
- Pull the baseline before beginning a new work session.
- Use a pull request; do not merge directly into the owner's branch.
- Do not modify existing migrations. Add the next numbered migration.
- Do not apply a new migration to the shared database without coordination.

Before every commit:

```bash
git status
git diff
git diff --cached
```

## 10. Common Setup Problems

### PowerShell blocks virtual-environment activation

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

This affects only the current terminal.

### API works but parsing never completes

The corresponding worker is not running, the AI provider failed, or MongoDB is
unreachable. Check `processing_error` and the worker terminal.

### `relation ... does not exist`

The required PostgreSQL migration has not been applied.

### MongoDB reports no replica-set primary

Check internet access, MongoDB Atlas IP access rules, credentials, and cluster
status.

### Neo4j connection reset

Retry the health check, confirm the Aura instance is running, and verify the
`neo4j+s://` URI and credentials.

### AI provider returns 400, 413, 503, or timeout

This can mean structured-output validation failure, token limits, provider
demand, or networking. The configured provider fallback may recover; otherwise
retry after inspecting the complete error.

## 11. Security Note

The repository previously tracked `backend/.env`. Removing it from the current
tree prevents future commits but does not erase old Git history. Credentials
should be replaced before broad or public repository access.
