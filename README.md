# Pyxis — Explainable AI Career Readiness & Internship Engine

Pyxis is an open-source, full-stack AI career platform designed to evaluate student resumes against real-world internship descriptions. Rather than relying on "black-box" LLM scoring, Pyxis decouples official match calculations from generative text model outputs—combining **deterministic canonical skill overlap**, **graph database relationship traversal**, **pgvector semantic similarity**, and **retrieval-augmented generation (RAG)** to provide transparent, evidence-backed readiness scores.

## Tech Stack & Polyglot Architecture

Pyxis leverages a **polyglot persistence design**, directing each data domain to its optimal storage engine:

* **Backend & APIs:** Python 3.11, FastAPI, SQLAlchemy ORM, Pydantic v2

* **Frontend:** React, TypeScript, Vite, Tailwind CSS

* **Relational State & Vector Database (PostgreSQL / Supabase):** Stores user accounts, JWT credentials, worker job queues, immutable match history, and `pgvector` section-level embeddings.

* **Document Database (MongoDB Atlas):** Stores raw extracted resume text, structured AI-parsed JSON schemas, and profile facts.

* **Graph Database (Neo4j Aura):** Maps canonical skills, aliases (`ALIAS_OF`), prerequisite pathways (`PREREQUISITE_FOR`), and curated evidence links (`EVIDENCE_FOR`).

* **AI & RAG Orchestration:** Multi-provider LLMs (OpenAI, Groq, Gemini) with strict JSON schema enforcement, `pgvector` semantic retrieval, and shadow evidence adjudication.

## System Design & Processing Workflow

```
[ Resume Upload (PDF/DOCX) ] ──┐
                              ├─► [ PostgreSQL Queue ] ──► [ Asynchronous Workers ]
[ Internship Description ]   ──┘                                  │
                                                                  ▼
[ Explanations & Interview ]  ◄── [ Matching Engine ] ◄── [ Polyglot Persistence ]
   (RAG + Gap Roadmaps)          (Rules + Graph + Vector)  (Postgres + Mongo + Neo4j)

```

1. **Non-Blocking Asynchronous Ingestion:** Resumes and internship postings return quick HTTP responses (`202 Accepted`). Background workers claim job rows from durable PostgreSQL queues to run PDF/DOCX extraction, LLM parsing, JSON validation, and vector embedding generation without blocking main API routes.

2. **Multi-Layered Matching Engine:**

   * **Layer 1 — Deterministic Canonical Overlap:** Direct matching of normalized skills (e.g., `js` $\rightarrow$ `JavaScript`).

   * **Layer 2 — Graph Relationship Traversal:** Queries Neo4j for related capabilities, prerequisite paths, and alias resolution with path-distance decay.

   * **Layer 3 — Semantic Similarity:** Uses `pgvector` embeddings to identify contextual alignment in project and experience text.

   * **Layer 4 — Shadow AI Adjudication:** Reviews missing requirements against retrieved resume passages to identify implicit evidence.

3. **Evidence Provenance & Profile Sync:** Extracted skills and experience items retain their exact source `resume_id` and section context, allowing profile edits or resume deletions without corrupting other data.

## Key Features

* **Resilient Background Processing:** Asynchronous workers handle document parsing and vector regeneration with exponential backoff retries.

* **Explainable Scorecards:** Breaks down match scores into exact technical coverage, partial graph credit, and soft skill categories.

* **Compact GitHub Portfolio Enrichment:** Fetches public GitHub profiles, languages, and decoded READMEs to generate match-specific portfolio evidence without triggering API rate limits.

* **Match-Driven Interview Preparation:** Generates targeted technical, behavioral, and gap-focused practice questions tied directly to specific resume-internship pairs.

* **RAG-Powered Career Roadmaps:** Matches missing technical capabilities against curated knowledge chunks to recommend actionable learning projects and resume improvements.

## API Endpoint Overview

### Resume & Profile Management

* `POST /resumes` — Upload PDF/DOCX resume and queue extraction worker.

* `GET /resumes/{id}/parsed-profile` — Fetch validated structured profile JSON.

* `GET /profile/facts` — Retrieve aggregated user skills and experience inventory.

* `POST /profile/facts/refresh` — Rebuild profile facts across active ready resumes.

### Internship Processing

* `POST /internships` — Submit job posting text and queue requirement parser.

* `GET /internships/{id}/parsed-requirements` — Read extracted technical and preferred requirements.

* `POST /internships/{id}/reparse` — Re-evaluate internship posting with updated prompt schemas.

### Matching & Explanations

* `POST /matches/preview` — Compute on-demand match calculation without persisting history.

* `POST /matches/analyses` — Calculate and store immutable, versioned match report.

* `POST /matches/adjudications` — Run shadow LLM evidence review for un-matched requirements.

* `POST /matches/explanations` — Generate RAG-backed student gap analysis and roadmap.

* `POST /matches/github-evidence` — Evaluate candidate GitHub repositories against specific job requirements.

### Career & Interview Modules

* `POST /career/recommendations` — Generate profile-level career guidance and skill path recommendations.

* `POST /interviews/preparations` — Build practice question sets from a saved match analysis.

* `POST /interviews/sessions` — Initiate an interactive mock interview session.

## Database Migrations

PostgreSQL schema changes are maintained sequentially in `docs/migrations/`:

```
docs/migrations/
├── 005_internship_inputs.sql
├── 006_match_analyses.sql
├── 007_semantic_embeddings.sql
├── 008_semantic_embedding_refresh_queue.sql
├── 009_llm_match_adjudications.sql
├── 010_match_explainability_knowledge.sql
├── 011_match_explanations.sql
├── 012_user_profile_resume_facts.sql
├── 013_career_recommendations.sql
├── 014_github_profile_snapshots.sql
├── 015_github_compact_snapshots.sql
├── 016_github_profile_analyses.sql
└── 017_github_match_evidence.sql

```

A consolidated SQL database schema is provided in `docs/postgres-schema.sql`.

## Local Setup & Execution Guide

### 1. Prerequisites

* Python 3.11+

* Node.js 18+ & npm

* PostgreSQL (with `pgvector` extension)

* MongoDB Atlas or local MongoDB instance

* Neo4j Aura or local Neo4j instance

### 2. Backend Setup

```
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy configuration template and populate credentials
cp .env.example .env

# Run FastAPI development server
uvicorn main:app --reload

```

### 3. Background Workers

Start the background job processors in separate terminal instances:

```
# Resume parsing worker
python -m workers.resume_worker

# Internship requirement worker
python -m workers.internship_worker

# Vector embedding refresh worker
python -m workers.semantic_embedding_worker

```

### 4. Seed Neo4j Skill Graph

```
python -m scripts.seed_neo4j_skill_graph

```

### 5. Frontend Setup

```
cd frontend
npm install
npm run dev

```
