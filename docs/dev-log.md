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
