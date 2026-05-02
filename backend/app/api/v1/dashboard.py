"""
Dashboard analytics API routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.database import get_db
from app.models.models import User, JobApplication, JobListing, ApplicationStatus
from app.core.security import get_current_user
from app.schemas.schemas import DashboardStatsResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats", response_model=DashboardStatsResponse)
def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total_applied = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id
    ).count()

    interviews = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.status == ApplicationStatus.INTERVIEW
    ).count()

    offers = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.status == ApplicationStatus.OFFER
    ).count()

    rejections = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.status == ApplicationStatus.REJECTED
    ).count()

    ghosted = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.status == ApplicationStatus.GHOSTED
    ).count()

    interview_rate = (interviews / total_applied * 100) if total_applied > 0 else 0
    offer_rate = (offers / total_applied * 100) if total_applied > 0 else 0

    platform_stats = db.query(
        JobListing.source_platform,
        func.count(JobApplication.id)
    ).join(JobApplication, JobListing.id == JobApplication.job_id).filter(
        JobApplication.user_id == current_user.id
    ).group_by(JobListing.source_platform).all()

    return {
        "total_applied": total_applied,
        "interviews": interviews,
        "offers": offers,
        "rejections": rejections,
        "ghosted": ghosted,
        "interview_rate": round(interview_rate, 1),
        "offer_rate": round(offer_rate, 1),
        "platform_breakdown": [{"platform": p, "count": c} for p, c in platform_stats],
    }
