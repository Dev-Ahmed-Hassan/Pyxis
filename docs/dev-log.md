# Dev Log

## 2026-05-17

- Created Supabase project
- Enabled pgvector extension
- Decided PostgreSQL will be source of truth
- Decided MongoDB Atlas will store AI/resume documents
- Planned to use cloud databases instead of local DB servers
- Created PostgreSQL Phase 1 tables in Supabase: users, candidate_profiles, recruiter_profiles, internships, resumes, and applications.
- Disabled Row Level Security (RLS) because authentication and authorization will be handled later through the FastAPI backend instead of Supabase policies.
- Created MongoDB Atlas free cluster for resume and AI-related document storage.
- Created a MongoDB database and `resumes` collection for flexible resume parsing and AI output data. The active generic database name is `career_assistant`.
- Created a dedicated MongoDB database user and stored its connection string privately.
- Created FastAPI backend skeleton and verified server startup locally.
- Added initial `/` and `/health` endpoints and confirmed Swagger docs are accessible.


- For windows :
- python -m venv .venv
- pip install -r requirements.txt


- - Fixed Supabase direct connection IPv6 issue by switching to the Session Pooler connection string.
- Confirmed FastAPI backend can successfully connect to Supabase PostgreSQL through `/health/postgres`.

- Confirmed FastAPI backend can successfully connect to MongoDB Atlas through `/health/mongo`.
- Current backend foundation is complete: local FastAPI app connects to Supabase PostgreSQL and MongoDB Atlas.


- Next step : create SQLAlchemy models → signup endpoint → password hashing → login/JWT

## 2026-06-01

- Added `instructions.md` as the contributor handoff and development operating
  manual.
- Documented local setup, private credential handling, database ownership,
  migration discipline, route and worker structure, partner onboarding,
  verification commands, and the current matching roadmap.
- Added a dictionary-backed related-skill evidence provider behind an interface.
  Match previews now explain curated relationships such as `Nmap` supporting
  `Network Security` without inflating the deterministic exact-overlap score.

## 2026-06-02

- Normalized domain-concept aliases and added short explainable relationship
  paths such as `Nessus -> Vulnerability Assessment -> Vulnerability Research`.
- Added capped partial credit for related concrete technical evidence while
  keeping exact overlap, related contribution, and domain evidence separate.
- Added manual-review warnings for broad requirements such as
  `Troubleshooting`.
- Added `matching_engine.md` as the living matching strategy and decision
  record. It documents the current score, known weaknesses, data limitations,
  evaluation rules, and ordered engine-improvement plan.
- Added a fixture-backed offline matching evaluator with a CLI report and
  deterministic synthetic IDs. The initial baseline covers eight reviewed
  cases across six domains and passes under score version
  `category-aware-related-skill-credit-v3`.
- Upgraded matching to `typed-weighted-related-skill-credit-v4`. Curated
  relationships now carry types and confidence values, indirect paths decay by
  distance, and each missing requirement receives numeric credit from its
  strongest reviewed path only.
- Upgraded matching to `provenance-weighted-related-skill-credit-v5`. Resume
  evidence now preserves skills-list, project, experience, certification, and
  cautious-inference provenance. Related credit uses the strongest provenance,
  while exact matches remain deterministic and auditable.
- Added migration `006_match_analyses.sql` and owned saved-analysis endpoints.
  PostgreSQL now stores immutable score versions and complete evidence
  breakdowns, while input-changing mutations mark affected history stale.
- Upgraded matching responses to `separate-semantic-evidence-reporting-v6`.
  Migration `007_semantic_embeddings.sql`, a Gemini embedding adapter, and
  `POST /matches/embeddings/refresh` now store explainable `768`-dimension
  pgvector evidence per resume section item and internship requirement.
  Semantic evidence remains separate from numeric scoring until calibration.
- Added migration `008_semantic_embedding_refresh_queue.sql` and a dedicated
  semantic embedding worker. Profile changes now invalidate old vectors and
  enqueue retryable regeneration without making validated parsing depend on
  Gemini availability. Queue generations discard obsolete in-flight results.
- Added a semantic-threshold calibration CLI and a clearly labeled synthetic
  starter corpus. Live reviewed observations remain required before semantic
  evidence can add numeric credit.
- Added migration `009_llm_match_adjudications.sql` and the shadow-only
  `POST /matches/adjudications` path. Semantic refresh now stores bullet-level
  resume passages and context-enriched requirement embeddings. The adjudicator
  may classify missed evidence only with retrieved resume citations; Python
  calculates a bounded comparison while the official v6 score remains unchanged.
- Added deadline-focused matcher stabilization: common cybersecurity/web aliases
  now normalize variants such as `Metasploit Framework`, `Burp Suite
  Professional`, `Python scripting`, and `HTML`, while v7 adjudication uses a
  compact audit prompt to avoid provider token-limit failures.
