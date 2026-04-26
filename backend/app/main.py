"""
AI Job Agent - FastAPI Backend
Production-ready API with modular routing.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

from app.models.database import engine
from app.models.models import Base
from app.config import get_settings

# Import all routers
from app.api.v1 import auth, profile, resume, jobs, applications, dashboard, alerts, credentials, networking, learning

settings = get_settings()

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Job Agent",
    description="Autonomous AI-powered job search and application system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS - reads from env or uses defaults
# Set CORS_ORIGINS=https://app1.com,https://app2.com in production
_cors_origins = os.getenv("CORS_ORIGINS", "")
if _cors_origins:
    allow_origins = [o.strip() for o in _cors_origins.split(",")]
else:
    allow_origins = [
        "http://localhost:3000",
        "http://frontend:3000",
        "https://localhost:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router, prefix="/api")
app.include_router(profile.router, prefix="/api")
app.include_router(resume.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(applications.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(credentials.router, prefix="/api")
app.include_router(networking.router, prefix="/api")
app.include_router(learning.router, prefix="/api")

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/")
def root():
    return {
        "name": "AI Job Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth": "/api/auth",
            "profile": "/api/profile",
            "resume": "/api/resume",
            "jobs": "/api/jobs",
            "applications": "/api/applications",
            "dashboard": "/api/dashboard",
            "alerts": "/api/alerts",
            "credentials": "/api/credentials",
            "networking": "/api/networking",
            "insights": "/api/insights"
        }
    }

if __name__ == "__main__:":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
