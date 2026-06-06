# API Workings And App Integration

This guide explains what each current API group does, whether it uses AI, what
it stores, and where it belongs in the application.

Except for root and health routes, endpoints require:

```text
Authorization: Bearer <access_token>
```

## 1. System And Authentication

| Endpoint | What happens |
|---|---|
| `GET /` | Confirms FastAPI is running. |
| `GET /health` | Confirms the process is responsive. |
| `GET /health/postgres` | Tests PostgreSQL. |
| `GET /health/mongo` | Tests MongoDB. |
| `GET /health/neo4j` | Tests Neo4j configuration and connectivity. |
| `POST /auth/signup` | Creates a PostgreSQL student account. |
| `POST /auth/login` | Validates credentials and returns a JWT bearer token. |
| `GET /auth/me` | Returns the authenticated account. |

These routes do not use AI or workers.

## 2. Student Profile And Profile Facts

### Editable profile

| Endpoint | Purpose |
|---|---|
| `GET /profile` | Read headline, bio, and target roles. |
| `PATCH /profile` | Update those user-entered fields. |

### Resume-derived facts

| Endpoint | Purpose |
|---|---|
| `GET /profile/facts` | Read already stored skills, projects, and certifications. |
| `POST /profile/facts/refresh` | Rebuild those stored facts from every active ready resume. |

`GET` is read-only. `refresh` deletes the user's old derived fact rows and
recreates them from parsed MongoDB resume documents. It does not call an LLM;
the resume was already parsed earlier. Normal successful resume parsing and
parsed-profile edits synchronize facts for that resume, while full refresh is
a repair/rebuild tool.

When a resume is deleted, facts linked to its `resume_id` are removed.

Frontend use: profile dashboard, skill inventory, projects, certifications,
career recommendations, and future profile-level features.

## 3. Resume APIs

| Endpoint | Purpose | AI/worker behavior |
|---|---|---|
| `POST /resumes` | Upload PDF/DOCX with an alias. | Queues processing; resume worker performs extraction and AI parsing. |
| `GET /resumes` | List active owned resumes. | Read-only. |
| `GET /resumes/{id}` | Poll status and errors. | Read-only. |
| `PATCH /resumes/{id}` | Change alias/default selection. | No AI. |
| `POST /resumes/{id}/retry` | Retry failed processing. | Resume worker must be running. |
| `GET /resumes/{id}/parsed-profile` | Read validated parsed JSON. | No new AI call. |
| `PATCH /resumes/{id}/parsed-profile` | Correct parsed profile manually. | No new parsing call; dependent data is invalidated/refreshed. |
| `DELETE /resumes/{id}` | Soft-delete resume and linked profile facts. | No AI. |

Processing flow:

```text
upload
-> PostgreSQL queue/status
-> resume worker
-> file text extraction
-> MongoDB raw text
-> AI structured parsing
-> canonical skills
-> MongoDB parsed profile
-> profile facts synchronization
-> semantic embedding refresh queued
-> ready
```

## 4. Internship APIs

| Endpoint | Purpose | AI/worker behavior |
|---|---|---|
| `POST /internships` | Save pasted description and queue parsing. | Internship worker calls AI. |
| `GET /internships` | List owned internship inputs. | Read-only. |
| `GET /internships/{id}` | Poll status and errors. | Read-only. |
| `POST /internships/{id}/retry` | Retry a failed job. | Worker required. |
| `POST /internships/{id}/reparse` | Parse again with the current schema/prompts. | Worker required; useful after parser changes. |
| `GET /internships/{id}/parsed-requirements` | Read structured requirements. | No new AI call. |
| `DELETE /internships/{id}` | Soft-delete the input and stale dependent analyses. | No AI. |

Processing flow:

```text
description
-> PostgreSQL queue/status
-> internship worker
-> AI structured parsing
-> canonical requirements
-> MongoDB parsed requirements
-> semantic embedding refresh queued
-> ready
```

## 5. Core Matching APIs

### `POST /matches/preview`

Input:

```json
{
  "resume_id": "uuid",
  "internship_id": "uuid"
}
```

Calculates the deterministic match on demand. It combines:

- canonical exact overlap;
- weighted required/preferred coverage;
- bounded related-skill credit from Neo4j or local reviewed graph data;
- stored semantic evidence for explanation only.

The LLM does not calculate this score. Preview is not saved as a match-analysis
row.

### `POST /matches/analyses`

Runs the same match calculation and saves an immutable analysis:

```json
{
  "resume_id": "uuid",
  "internship_id": "uuid",
  "analysis_session_id": null
}
```

Omit `analysis_session_id` or send `null`; the backend creates one. Do not send
an empty string because it is not a UUID.

Use saved analysis IDs as the stable center of the analysis dashboard and
downstream features.

### Saved analysis reads

| Endpoint | Purpose |
|---|---|
| `GET /matches/analyses` | List saved analyses for the user. |
| `GET /matches/analyses/{analysis_id}` | Reopen one dashboard. |
| `GET /matches/analyses/{analysis_id}/learning-paths` | Build deterministic graph learning paths for its missing skills. |

Learning paths use Neo4j with local graph fallback. They do not call AI and are
not stored as another analysis record.

## 6. Match Embeddings And Semantic Evidence

### `POST /matches/embeddings/refresh`

Embeds structured resume sections and internship requirements for one pair.
It stores vectors in PostgreSQL/pgvector. The endpoint performs the refresh
directly; automatic refresh jobs are handled by `semantic_embedding_worker`.

Embeddings retrieve fuzzy supporting passages such as project or experience
text. They are reported separately and do not directly change the official
score.

### Knowledge embeddings

| Endpoint | Purpose |
|---|---|
| `POST /matches/explainability/knowledge/embeddings/refresh` | Chunk and embed curated files from the knowledge base. |
| `POST /matches/explainability/knowledge/search` | Embed a query and return the most similar knowledge chunks. |

These vectors are a separate pool from resume/internship vectors. They supply
grounded guidance for explanations and career recommendations. Refresh does
not require the semantic worker.

## 7. AI Match Review And Explanation

### `POST /matches/adjudications`

Uses retrieved resume evidence and an LLM to review requirements that the
deterministic matcher may have underestimated. It produces:

- requirement judgments;
- bounded shadow score;
- fairness audit;
- cited evidence.

The shadow score currently does not replace the official score. The result is
saved and returned by `GET /matches/adjudications/{id}`.

### `POST /matches/explanations`

Input:

```json
{
  "analysis_id": "saved-match-analysis-uuid",
  "adjudication_id": "optional-adjudication-uuid"
}
```

Uses the saved match, optional adjudication, retrieved knowledge chunks, and an
LLM to create UI-oriented:

- score explanation;
- strengths and partial matches;
- gaps and resume improvements;
- project ideas;
- interview talking points.

It saves the result. Retrieve it with
`GET /matches/explanations/{explanation_id}`.

Recommended dashboard sequence:

```text
create saved analysis
-> optionally create adjudication
-> create explanation
-> load learning paths
-> optionally create GitHub match evidence
```

## 8. Career APIs

### `GET /career/graph-recommendations?limit=8`

Deterministic profile-level role matching:

```text
stored profile facts
-> Neo4j role requirements and relationships
-> ranked role cards and graph learning gaps
```

No AI call and no saved recommendation row.

### `POST /career/recommendations`

AI/RAG profile-level guidance:

```json
{
  "target_field": "Cyber Security",
  "preferred_roles": ["SOC Analyst", "Penetration Tester"]
}
```

It compacts profile facts, retrieves relevant knowledge chunks, calls the
configured LLM, and stores detailed career paths, projects, gaps, and roadmap.
Read a saved result with `GET /career/recommendations/{id}`.

The difference is:

- graph recommendations are fast, deterministic role matching;
- POST recommendations are richer AI guidance grounded by RAG.

Neither endpoint is tied to one internship match.

## 9. GitHub APIs

### Core scan

`POST /github/snapshots` calls the public GitHub API and stores:

- raw profile/repository/language/README payloads;
- an automatically produced compact snapshot.

There is no separate compact-creation endpoint.

Snapshot reads:

```text
GET /github/snapshots/latest
GET /github/snapshots/latest/compact
GET /github/snapshots/{snapshot_id}
GET /github/snapshots/{snapshot_id}/compact
```

For routes accepting `snapshot_id`, use the original snapshot ID. The compact
response uses the same snapshot identity; it is a representation, not an
independent scan.

### Profile-level GitHub analysis

`POST /github/analyses` uses a compact snapshot and AI:

```json
{
  "snapshot_id": "optional-snapshot-uuid",
  "target_field": "Cyber Security",
  "preferred_roles": ["Security Analyst"],
  "force_refresh": false
}
```

Without `snapshot_id`, it uses the latest snapshot. With `force_refresh=false`,
an existing analysis with the same snapshot and request can be returned.
`force_refresh=true` reruns the LLM analysis but does not fetch GitHub again.
Create a new snapshot first when fresh GitHub API data is required.

Read results:

```text
GET /github/analyses/latest
GET /github/analyses/{analysis_id}
```

### Match-specific GitHub evidence

`POST /matches/github-evidence` compares a saved match with a compact GitHub
snapshot through AI:

```json
{
  "match_analysis_id": "uuid",
  "github_snapshot_id": null,
  "force_refresh": false
}
```

It returns relevant repositories, requirement support, application talking
points, and interview questions. It is optional; matching and interviews must
still work without GitHub.

Read it with:

```text
GET /matches/github-evidence/latest?match_analysis_id=<uuid>
GET /matches/github-evidence/{evidence_id}
```

## 10. Frontend Workflow

```text
login
-> upload/poll resume
-> create/poll internship
-> preview match
-> save analysis
-> show analysis dashboard
   -> explanation
   -> learning paths
   -> optional GitHub evidence
   -> interview preparation
```

Profile-side workflow:

```text
profile facts
-> graph career cards
-> optional AI/RAG career recommendation
-> optional GitHub snapshot and portfolio analysis
```

The frontend should fetch saved results when reopening pages. It should not
recreate AI analyses on every render.
