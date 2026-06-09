# Frontend Feature Coverage

This checklist maps the existing backend to planned frontend surfaces. Update
it as each workflow is connected so implemented backend capabilities are not
lost behind missing UI.

Status meanings:

- `Done`: usable frontend workflow exists.
- `Foundation`: route or placeholder exists, but feature data is not connected.
- `Planned`: backend exists and the frontend still needs implementation.
- `Teammate`: backend is being developed separately.

## Public And Authentication

| Frontend surface | Backend APIs | Status |
|---|---|---|
| Product landing page | None | Done |
| Signup | `POST /auth/signup` | Done |
| Login and logout | `POST /auth/login`, `GET /auth/me` | Done |
| Protected application shell | JWT authentication | Done |

## Profile And Resumes

| Frontend surface | Backend APIs | Status |
|---|---|---|
| Resume library | `GET /resumes`, `GET /resumes/{id}` | Done |
| Resume upload and status | `POST /resumes`, polling `GET /resumes/{id}` | Done |
| Resume retry and deletion | `POST /resumes/{id}/retry`, `DELETE /resumes/{id}` | Foundation: retry connected; deletion remains |
| Parsed resume viewer/editor | `GET/PATCH /resumes/{id}/parsed-profile` | Foundation: viewer connected; editor remains |
| Editable profile | `GET/PATCH /profile` | Planned |
| Aggregated profile facts | `GET /profile/facts` | Planned |
| Profile-facts rebuild | `POST /profile/facts/refresh` | Planned |

## Internships

| Frontend surface | Backend APIs | Status |
|---|---|---|
| Internship library and input | `GET/POST /internships` | Done |
| Parsing status and details | `GET /internships/{id}` | Done |
| Retry and reparse controls | `POST /internships/{id}/retry`, `/reparse` | Done |
| Parsed requirements viewer | `GET /internships/{id}/parsed-requirements` | Done |
| Internship deletion | `DELETE /internships/{id}` | Done |

## Match Workspace

| Frontend surface | Backend APIs | Status |
|---|---|---|
| Resume/internship selection | Resume and internship list APIs | Done |
| Match preview | `POST /matches/preview` | Done |
| Saved analysis creation | `POST /matches/analyses` | Done |
| Analysis history and reopen | `GET /matches/analyses`, `GET /matches/analyses/{id}` | Foundation: history and stored-payload reopen connected |
| Semantic evidence refresh | `POST /matches/embeddings/refresh` | Planned as an advanced/recovery action |
| Graph learning paths | `GET /matches/analyses/{id}/learning-paths` | Done |

## Explainability And Guidance

| Frontend surface | Backend APIs | Status |
|---|---|---|
| AI evidence adjudication | `POST /matches/adjudications`, saved adjudication read | Done |
| Why-this-score explanation | `POST/GET /matches/explanations` | Done |
| Strengths and partial matches | Saved explanation payload | Done |
| Gap severity and resume improvements | Saved explanation payload | Done |
| Suggested learning projects | Saved explanation payload | Done |
| Interview talking points | Saved explanation payload | Done |
| Knowledge search | Explainability knowledge search API | Internal/admin UI only |
| Knowledge embedding refresh | Knowledge refresh API | Internal/admin UI only |

## Career Direction

| Frontend surface | Backend APIs | Status |
|---|---|---|
| Deterministic role-fit cards | `GET /career/graph-recommendations` | Planned |
| AI/RAG career recommendation | `POST /career/recommendations` | Planned |
| Saved career recommendation | `GET /career/recommendations/{id}` | Planned |
| Career gaps and roadmap | Both career recommendation responses | Planned |

## GitHub Portfolio

| Frontend surface | Backend APIs | Status |
|---|---|---|
| GitHub profile scan | `POST /github/snapshots` | Planned |
| Latest/full/compact snapshots | GitHub snapshot GET APIs | Planned |
| Profile-level portfolio analysis | `POST /github/analyses` and analysis GET APIs | Planned |
| Match-specific GitHub evidence | `POST /matches/github-evidence` and evidence GET APIs | Planned |
| Repository talking points/questions | GitHub match-evidence payload | Planned |

## Interview Preparation

| Frontend surface | Backend APIs | Status |
|---|---|---|
| Prepared interview set | Interview module endpoints | Teammate |
| Live text interview | Interview session endpoints | Teammate |
| Collective final evaluation | Interview evaluation endpoint | Teammate |
| Voice input/output | Future adapter | Planned later |

## Recommended Frontend Build Order

1. Authenticated application shell and navigation.
2. Resume and internship libraries with processing status.
3. New-match workflow and saved analysis dashboard.
4. Explanation, learning paths, and actionable improvements.
5. Profile facts and career direction.
6. GitHub profile and match-specific evidence.
7. Interview preparation after the teammate API contract is ready.

The frontend should fetch saved analyses when reopening a page. It should not
rerun AI generation automatically on every render.
