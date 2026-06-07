# Career Assistant Architecture Brief

## 1. Purpose

The career assistant is an internship application-readiness platform. The backend should help users create accounts, store profiles, upload resumes, parse resume data, and compare resumes with internship descriptions in a way that can be explained and defended.

This document is the project’s working architecture map. It is meant to keep the system understandable before it becomes large.

## 2. One-Sentence Architecture

FastAPI is the backend API, PostgreSQL stores core structured application data, MongoDB stores flexible resume and AI-related documents, and AI services are used for parsing and matching.

## 3. Current State

The current backend is small and clear:

- `backend/main.py` starts the FastAPI app and exposes health endpoints.
- `backend/database/postgres.py` checks the PostgreSQL connection.
- `backend/database/mongodb.py` checks the MongoDB connection.

At this stage, the project is mostly infrastructure and connection plumbing, not a full product yet.

## 4. Technology Roles

### FastAPI

FastAPI is the HTTP layer. It should receive requests from the frontend or other clients, validate inputs, call the correct service logic, and return JSON responses.

### PostgreSQL

PostgreSQL is the source of truth for structured data such as users, candidate profiles, recruiter profiles, internships, and applications.

### MongoDB

MongoDB stores flexible documents such as parsed resume payloads, extracted skills, AI analysis results, and other data that may change shape over time.

### AI / Parsing Layer

AI should not be the entire architecture. It should only be used where the input is unstructured and where structured rules are not enough, such as resume parsing, skill extraction, and ranking explanations.

## 5. Data Ownership

### PostgreSQL should own

- user accounts
- password hashes
- candidate and recruiter profiles
- internships
- applications
- relationship data between entities

### MongoDB should own

- raw resume uploads
- parsed resume text
- AI extraction output
- intermediate analysis documents
- flexible metadata that may change often

### Avoid duplication unless necessary

If the same information exists in both databases, one system must be the source of truth. PostgreSQL should usually win for final application state. MongoDB should support document-style processing, not replace core relational data.

## 6. Request Flow

### Example: login

1. Frontend sends email and password to FastAPI.
2. FastAPI validates the input.
3. PostgreSQL is queried for the user record.
4. The password hash is verified.
5. FastAPI returns a token or an error.

### Example: resume upload

1. Frontend uploads a resume file.
2. FastAPI receives the file and stores the raw document or extracted content in MongoDB.
3. A parsing step extracts structured fields such as name, skills, experience, and education.
4. Important final profile data can then be written or updated in PostgreSQL.

### Example: internship matching

1. User profile and resume data are loaded.
2. Internship data is fetched from PostgreSQL.
3. AI or rule-based matching computes a score.
4. The backend returns ranked results and a short explanation.

## 7. Backend Module Boundaries

The backend should grow in layers:

- route layer: receives HTTP requests
- service layer: contains business logic
- database layer: talks to PostgreSQL or MongoDB
- utility layer: handles hashing, token creation, parsing helpers, or shared validation

The goal is to keep request handling separate from business rules. If a file becomes difficult to explain, it is probably doing too much.

## 8. MVP Feature Order

Build the system in this order so each piece stays understandable:

1. health checks and database connections
2. signup and login
3. password hashing and JWT auth
4. profile creation and update
5. internship creation and listing
6. resume upload and storage
7. resume parsing
8. matching and scoring

Each step should be usable on its own before the next one is added.

## 9. Team Split

If the project is shared with a partner, split by responsibility, not by random tasks.

### Good split

- Person A: authentication, PostgreSQL schema, API contracts
- Person B: frontend, resume upload flow, AI parsing UI, presentation layer

### Shared decisions

- database schema changes
- API request and response formats
- what belongs in PostgreSQL versus MongoDB
- how matching scores are explained

### Avoid

- two people editing the same route without a contract
- building frontend screens before the API shape is known
- adding AI features before the data model exists

## 10. Understanding Checks

Before adding a feature, answer these questions:

- What problem does this feature solve?
- Which database owns the data?
- Which file should contain the logic?
- What is the input and output?
- How do I test it with one request?

If these answers are unclear, the feature is too large and should be split.

## 11. What This Project Is Not Yet

The career assistant is not yet:

- a full AI platform
- a complex microservices system
- a finished production application
- a project that should be built by copying generated code without understanding it

It is currently a small backend foundation that should grow through controlled steps.

## 12. Working Rule

Do not add a new layer until the previous one can be explained in plain language.

If you cannot explain how a request travels through the system, stop and simplify before adding more code.
