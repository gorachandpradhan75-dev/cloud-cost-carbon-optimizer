from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.aws import router as aws_router
from app.core.database import Base, engine
from app.models.optimization_scan import OptimizationScan


# Create database tables
Base.metadata.create_all(bind=engine)


# Create FastAPI application
app = FastAPI(
    title="Cloud Cost & Carbon Optimizer API",
    description=(
        "Backend API for AI-Driven Cloud FinOps and "
        "Sustainable Resource Optimization Platform"
    ),
    version="1.0.0",
)


# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include AWS API routes
app.include_router(aws_router)


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