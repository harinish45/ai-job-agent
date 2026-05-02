"""
Networking & Outreach API routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.models import User, UserProfile
from app.core.security import get_current_user
from app.services.networking import NetworkingService

router = APIRouter(prefix="/networking", tags=["networking"])

@router.post("/linkedin-connect")
async def generate_linkedin_connect(
    recruiter_name: str,
    recruiter_title: str,
    company: str,
    job_title: str = None,
    shared_interest: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    service = NetworkingService()

    message = await service.generate_linkedin_connect(
        candidate_name=current_user.full_name or "Candidate",
        candidate_title=profile.parsed_resume.get("title", "") if profile and profile.parsed_resume else "",
        recruiter_name=recruiter_name,
        recruiter_title=recruiter_title,
        company=company,
        job_title=job_title,
        shared_interest=shared_interest
    )

    return {"message": message, "character_count": len(message)}

@router.post("/recruiter-followup")
async def generate_recruiter_followup(
    job_title: str,
    company: str,
    days_since_apply: int,
    key_qualification: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = NetworkingService()
    message = await service.generate_recruiter_followup(
        candidate_name=current_user.full_name or "Candidate",
        job_title=job_title,
        company=company,
        days_since_apply=days_since_apply,
        key_qualification=key_qualification
    )
    return {"message": message}

@router.post("/referral-request")
async def generate_referral_request(
    contact_name: str,
    company: str,
    job_title: str,
    relationship: str = "former_colleague",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    service = NetworkingService()

    message = await service.generate_referral_request(
        candidate_name=current_user.full_name or "Candidate",
        candidate_title=profile.parsed_resume.get("title", "") if profile and profile.parsed_resume else "",
        contact_name=contact_name,
        company=company,
        job_title=job_title,
        relationship=relationship
    )
    return {"message": message}

@router.post("/thank-you")
async def generate_thank_you(
    interviewer_name: str,
    company: str,
    job_title: str,
    specific_topic: str = None,
    current_user: User = Depends(get_current_user)
):
    service = NetworkingService()
    message = await service.generate_thank_you(
        candidate_name=current_user.full_name or "Candidate",
        interviewer_name=interviewer_name,
        company=company,
        job_title=job_title,
        specific_topic=specific_topic
    )
    return {"message": message}
