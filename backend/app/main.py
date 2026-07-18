from fastapi import FastAPI
from sqlalchemy import text

from app.core.database import engine


app = FastAPI(
    title="Cloud Cost & Carbon Optimizer API",
    description="Backend API for AI-Driven Cloud FinOps and Sustainable Resource Optimization Platform",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "Cloud Cost & Carbon Optimizer API is running",
        "status": "healthy",
    }


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception as e:
        print(f"Database connection error: {e}")

        return {
            "status": "unhealthy",
            "database": "disconnected",
        }