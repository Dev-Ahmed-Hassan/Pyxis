# Pyxis Backend Workflows

This guide follows the current code. PostgreSQL stores durable ownership and queue
state. MongoDB stores the larger extracted and parsed documents. The API returns
quickly after accepting input, while separate workers perform slower extraction
and AI parsing work.

## Resume Upload Workflow

1. The frontend sends an authenticated `POST /resumes` multipart request with a
   PDF or DOCX file and a user-facing alias. The route is defined in
   [`backend/api/resumes.py`](../backend/api/resumes.py).
2. FastAPI resolves the bearer token through
   [`backend/api/auth.py`](../backend/api/auth.py). The current user is passed
   into the service rather than accepted from the request body.
3. [`backend/services/resume_service.py`](../backend/services/resume_service.py)
   enforces upload rules, creates a unique server filename, saves the file under
   `backend/uploads/<user-id>/`, and creates the PostgreSQL resume row.
4. [`backend/models/resume.py`](../backend/models/resume.py) stores the uploader
   as `user_id`, along with the local path and processing status. Routes fetch
   resumes through ownership checks, so one student cannot read another
   student's resumes through the API.
5. [`backend/workers/resume_worker.py`](../backend/workers/resume_worker.py)
   claims queued work. It can resume after failures because PostgreSQL records
   the current status, attempts, timestamps, and retry time.
6. [`backend/services/resume_extraction_service.py`](../backend/services/resume_extraction_service.py)
   extracts PDF or DOCX text and stores the raw text document in MongoDB.
7. [`backend/services/resume_parsing_service.py`](../backend/services/resume_parsing_service.py)
   sends the untrusted resume text to the configured AI provider route. The
   prompt rules live in
   [`backend/services/ai/prompt_security.py`](../backend/services/ai/prompt_security.py),
   the strict response schema lives in
   [`backend/services/ai/schemas.py`](../backend/services/ai/schemas.py), and
   fallback provider selection lives in
   [`backend/services/ai/orchestrator.py`](../backend/services/ai/orchestrator.py).
8. [`backend/services/skill_canonicalizer.py`](../backend/services/skill_canonicalizer.py)
   normalizes aliases such as `js` to `JavaScript` while preserving the
   original extracted text. MongoDB then holds raw text, validated parsed JSON,
   parser metadata, and prompt-security findings.
9. PostgreSQL reaches `ready` only after the worker completes the pipeline. The
   frontend can poll resume metadata and request the parsed profile when it is
   ready. A student may correct the AI-produced profile through the profile
   patch endpoint without editing the uploaded source file.

Run the resume worker from `backend/`:

```bash
python -m workers.resume_worker
```

## Internship Description Workflow

1. The frontend sends an authenticated `POST /internships` JSON request with a
   label, pasted internship description, and optional application URL. The
   route is defined in
   [`backend/api/internships.py`](../backend/api/internships.py).
2. [`backend/schemas/internship.py`](../backend/schemas/internship.py) validates
   the input length and URL. The current authenticated user still comes from the
   bearer token.
3. [`backend/services/internship_service.py`](../backend/services/internship_service.py)
   creates the PostgreSQL row with the authenticated student's `user_id`.
   [`backend/models/internship.py`](../backend/models/internship.py) stores the
   pasted description, ownership, processing state, retry fields, and MongoDB
   reference.
4. [`backend/workers/internship_worker.py`](../backend/workers/internship_worker.py)
   claims submitted descriptions independently of the API request.
5. [`backend/services/internship_parsing_service.py`](../backend/services/internship_parsing_service.py)
   sends the untrusted description through the configurable AI fallback chain,
   validates it with
   [`backend/services/ai/internship_schemas.py`](../backend/services/ai/internship_schemas.py),
   canonicalizes required and preferred skills, and stores the structured
   document in MongoDB.
6. PostgreSQL reaches `ready` after successful validation. The authenticated
   owner can retrieve the structured requirements through
   `GET /internships/{internship_id}/parsed-requirements`.

Run the internship worker from `backend/`:

```bash
python -m workers.internship_worker
```

## Why Internship Input Starts As Text

Most internship postings are page text, form text, or messages rather than
downloadable documents. Pasted descriptions therefore keep the first matching
version focused. A later document-upload endpoint can reuse the same PDF and
DOCX extraction adapter used by resumes, then pass the extracted text into the
existing internship parsing service. The storage and matching layers do not
need to be redesigned.

## Basic Match Preview Workflow

1. The frontend sends an authenticated `POST /matches/preview` request with a
   ready resume ID and a ready internship ID. The route is defined in
   [`backend/api/matches.py`](../backend/api/matches.py).
2. [`backend/services/matching_service.py`](../backend/services/matching_service.py)
   reuses the existing resume and internship profile services. Those services
   verify that both records belong to the authenticated student, have not been
   soft deleted, and have reached `ready`.
3. The service reads the validated parsed documents from MongoDB and
   canonicalizes skills defensively. This means aliases such as `js` and
   `JavaScript` compare as the same skill even when an older MongoDB document is
   encountered.
4. Required-skill coverage contributes `80%` and preferred-skill coverage
   contributes `20%`. If one section is absent, its unused weight is reassigned
   to the available section. If both are absent, the score is `0` and the
   response includes warnings.
5. Concrete technical skills contribute to this first exact-overlap score.
   Broad domain concepts and soft skills are returned separately. Soft skills
   cannot reduce the technical score.
6. [`backend/services/related_skill_service.py`](../backend/services/related_skill_service.py)
   checks a small curated rule set behind an interface. It normalizes aliases
   such as `Network Security Principles` to `Network Security` and follows
   short explainable paths such as
   `Nessus -> Vulnerability Assessment -> Vulnerability Research`.
7. Related evidence for a missing concrete technical requirement contributes
   confidence-weighted partial credit capped at `50%` of that requirement's
   normal value. Indirect paths decay by `0.85` per additional edge. The
   strongest reviewed path determines numeric credit while alternative paths
   remain visible. Domain concepts remain explanatory only. Neo4j can later
   replace the dictionary-backed provider incrementally.
8. [`backend/services/resume_evidence_service.py`](../backend/services/resume_evidence_service.py)
   inventories canonical evidence from the skills list, projects, experience,
   and certification names. Related evidence demonstrated in experience or a
   project receives more weight than a bare mention or cautious inference.
   Exact matches remain deterministic while returning their strongest evidence
   for explanation.
9. [`backend/services/semantic_matching_service.py`](../backend/services/semantic_matching_service.py)
   loads strongest pgvector similarity evidence for each concrete requirement
   when refreshed embeddings are available. Each item names the resume section,
   source excerpt, model, similarity, and reporting threshold. Semantic
   evidence remains separate and does not add points before calibration.
10. The response returns the overall score, exact-overlap subtotal,
   related-skill contribution, applied weights, resume skills, categorized
   requirements, evidence provenance, evidence paths, and warnings. The LLM
   does not calculate this score.

Example request:

```json
{
  "resume_id": "your-ready-resume-uuid",
  "internship_id": "your-ready-internship-uuid"
}
```

This endpoint calculates a read-only preview on demand.

## Semantic Embedding Refresh Workflow

1. Apply `docs/migrations/007_semantic_embeddings.sql` and
   `docs/migrations/008_semantic_embedding_refresh_queue.sql`, then configure
   `EMBEDDING_MODEL_ROUTE=gemini:gemini-embedding-001`.
2. Send `POST /matches/embeddings/refresh` with one owned ready resume ID and
   internship ID.
3. [`backend/services/semantic_embedding_service.py`](../backend/services/semantic_embedding_service.py)
   deterministically assembles listed skills, each summary, project, experience,
   education, and certification item, plus each concrete required or preferred
   internship skill. Project and experience bullets receive their own passages
   so retrieval can cite focused evidence.
4. The configured Gemini adapter generates `768`-dimension vectors. PostgreSQL
   replaces the pair's pgvector rows transactionally and marks older analyses
   stale.
5. Subsequent previews report the strongest section evidence above the current
   threshold independently of the numeric score.
6. Successful parser runs and relevant manual resume edits invalidate old
   vectors and enqueue asynchronous regeneration. Run:

```bash
python -m workers.semantic_embedding_worker
```

7. The worker retries provider or storage failures independently of parsing.
   A generation token discards obsolete results if a newer edit arrives while
   an older job is still embedding.
8. Export live comparisons for human review:

```bash
python -m scripts.export_semantic_calibration_candidates \
  --resume-id RESUME_UUID \
  --internship-id INTERNSHIP_UUID
```

   Exported observations remain `pending_review` with no label. Only move
   reviewed rows into `tests/fixtures/semantic_calibration_cases.json` after
   setting `should_report`, changing `source` to `reviewed_live`, and recording
   a reviewer note.

## Shadow LLM Evidence Adjudication Workflow

1. Apply `docs/migrations/009_llm_match_adjudications.sql`, configure
   `LLM_MATCH_ADJUDICATOR_PRIMARY` and optional fallbacks, then refresh the
   selected input embeddings.
2. Send `POST /matches/adjudications` with an owned ready resume ID and
   internship ID.
3. [`backend/services/match_llm_adjudication_service.py`](../backend/services/match_llm_adjudication_service.py)
   runs the official deterministic preview, selects each missing concrete
   requirement, and asks
   [`backend/services/semantic_matching_service.py`](../backend/services/semantic_matching_service.py)
   for its top three resume passages even when they are below the normal
   semantic reporting threshold.
4. The configured structured-output LLM classifies each missing requirement as
   `direct`, `strong_partial`, `weak_related`, or `absent`. Every supported
   judgment must cite a retrieved resume passage. Unknown requirements,
   duplicate judgments, missing judgments, and uncited evidence are rejected.
5. Python converts the validated labels into a bounded shadow comparison.
   `direct` is capped at `50%` of a requirement, `strong_partial` at `30%`, and
   weak or absent evidence receives no points. The official score is unchanged.
6. PostgreSQL stores the immutable audit row with model, prompt version,
   retrieved excerpts, citations, judgments, fairness audit, official score,
   and shadow score. `GET /matches/adjudications/{adjudication_id}` returns an
   owned saved audit. Input changes mark prior audits stale.

## Saved Match Analysis Workflow

1. The frontend sends `POST /matches/analyses` with a ready resume ID, ready
   internship ID, and optional `analysis_session_id`.
2. [`backend/services/match_analysis_service.py`](../backend/services/match_analysis_service.py)
   runs the same owned-input deterministic calculation as preview and stores an
   immutable PostgreSQL row with the score version, overall score, complete JSON
   evidence breakdown, creation time, and optional stale time.
3. `GET /matches/analyses` and `GET /matches/analyses/{analysis_id}` return
   authenticated-student-owned history only.
4. [`backend/services/analysis_staleness_service.py`](../backend/services/analysis_staleness_service.py)
   marks affected history stale when parsed resume content changes or resume
   and internship inputs are deleted, retried, or reparsed. Historical payloads
   remain unchanged for auditing.

When the internship parser schema changes, queue a ready or failed description
again without deleting it:

```text
POST /internships/{internship_id}/reparse
```

## Offline Matching Evaluation Workflow

1. Human-reviewed synthetic cases live in
   [`backend/tests/fixtures/matching_engine_cases.json`](../backend/tests/fixtures/matching_engine_cases.json).
   Each case provides parsed skill names plus expected score ranges, evidence
   paths, and warning fragments.
2. [`backend/services/matching_evaluation_service.py`](../backend/services/matching_evaluation_service.py)
   converts each case into validated synthetic resume and internship documents,
   runs the same deterministic matching function used by the API, and compares
   the response with the reviewed expectations.
3. Run the readable report from `backend/`:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m scripts.evaluate_matching_engine
```

Use `--json` for the complete machine-readable report. Add a fixture whenever
manual testing exposes a matching weakness. Do not tune global weights around
one resume or internship.

## Storage Summary

PostgreSQL is the authoritative source for accounts, ownership, queue state,
soft deletion, retries, and MongoDB document references. MongoDB stores raw
resume text and structured AI output because those documents may evolve as the
parser schema grows. Neo4j is planned for a later matching stage: canonical
skills and the current curated relationships become graph nodes and edges so
Pyxis can suggest prerequisites and learning paths when explaining a gap.
