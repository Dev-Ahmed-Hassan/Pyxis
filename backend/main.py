from fastapi import FastAPI, HTTPException

from api.auth import router as auth_router
from api.career import router as career_router
from api.github import router as github_router
from api.interviews import router as interviews_router
from api.internships import router as internships_router
from api.matches import router as matches_router
from api.profile import router as profile_router
from api.resumes import router as resumes_router
from database.postgres import check_postgres_connection
from database.mongodb import check_mongodb_connection
from database.neo4j import check_neo4j_connection, is_neo4j_configured

app = FastAPI(title="Backend")
app.include_router(auth_router)
app.include_router(career_router)
app.include_router(github_router)
app.include_router(interviews_router)
app.include_router(internships_router)
app.include_router(matches_router)
app.include_router(profile_router)
app.include_router(resumes_router)


@app.get("/")
def root():
    return {
        "message": "Backend running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/health/postgres")
def postgres_health():
    try:
        connected = check_postgres_connection()

        return {
            "database": "postgres",
            "connected": connected
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"PostgreSQL connection failed: {str(error)}"
        )


@app.get("/health/mongo")
def mongo_health():
    try:
        connected = check_mongodb_connection()

        return {
            "database": "mongodb",
            "connected": connected
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"MongoDB connection failed: {str(error)}"
        )


@app.get("/health/neo4j")
def neo4j_health():
    if not is_neo4j_configured():
        raise HTTPException(
            status_code=503,
            detail="Neo4j is not configured",
        )
    try:
        return {
            "database": "neo4j",
            "connected": check_neo4j_connection(),
        }
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Neo4j connection failed: {str(error)}",
        )
