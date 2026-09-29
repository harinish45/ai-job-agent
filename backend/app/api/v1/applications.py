"""
Application tracking API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.models.database import get_db
from app.models.models import User, UserProfile, JobListing, JobApplication, ApplicationStatus
from app.core.security import get_current_user
from app.schemas.schemas import (
    ApplicationCreate, ApplicationStatusUpdate,
    ApplicationResponse, ApplicationListResponse
)

router = APIRouter(prefix="/applications", tags=["applications"])

@router.get("", response_model=ApplicationListResponse)
def get_applications(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(JobApplication).filter(JobApplication.user_id == current_user.id)

    if status:
        query = query.filter(JobApplication.status == ApplicationStatus(status))

    applications = query.order_by(JobApplication.created_at.desc()).all()

    result = []
    for app in applications:
        job = db.query(JobListing).filter(JobListing.id == app.job_id).first()
        result.append({
            "id": app.id,
            "job_title": job.title if job else "Unknown",
            "company": job.company if job else "Unknown",
            "status": app.status.value,
            "applied_at": app.applied_at,
            "auto_applied": app.auto_applied,
            "next_follow_up": app.next_follow_up_date,
            "source_platform": job.source_platform if job else None,
        })

    return {"applications": result}

@router.post("/jobs/{job_id}/apply")
def apply_to_job(
    job_id: int,
    data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id,
        JobApplication.job_id == job_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Already applied to this job")

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

    if data.auto_apply and profile and profile.auto_apply_enabled:
        status = ApplicationStatus.PENDING_APPROVAL
        auto_applied = True
    else:
        status = ApplicationStatus.SAVED
        auto_applied = False

    application = JobApplication(
        user_id=current_user.id,
        job_id=job_id,
        status=status,
        auto_applied=auto_applied,
        status_history=[{
            "status": status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Application created"
        }]
    )
    db.add(application)
    db.commit()

    return {
        "application_id": application.id,
        "status": status.value,
        "auto_applied": auto_applied,
        "message": "Application queued" if auto_applied else "Application saved for manual review"
    }

@router.put("/{app_id}/status")
def update_status(
    app_id: int,
    data: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    application = db.query(JobApplication).filter(
        JobApplication.id == app_id,
        JobApplication.user_id == current_user.id
    ).first()

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    application.status = data.status
    history = application.status_history or []
    history.append({
        "status": data.status.value,
        "timestamp": datetime.utcnow().isoformat(),
        "note": data.note or "Status updated"
    })
    application.status_history = history

    if data.status == ApplicationStatus.APPLIED:
        application.applied_at = datetime.utcnow()

    db.commit()
    return {"status": "updated"}
