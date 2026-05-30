from fastapi import FastAPI, HTTPException

from api.auth import router as auth_router
from api.profile import router as profile_router
from api.resumes import router as resumes_router
from database.postgres import check_postgres_connection
from database.mongodb import check_mongodb_connection

app = FastAPI(title="Backend")
app.include_router(auth_router)
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
