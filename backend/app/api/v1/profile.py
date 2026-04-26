"""
Profile API routes.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.models import User, UserProfile, WorkMode, ExperienceLevel
from app.core.security import get_current_user
from app.schemas.schemas import ProfileUpdate, ProfileResponse, ResumeAnalysisResponse

router = APIRouter(prefix="/profile", tags=["profile"])

@router.get("", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return {
        "id": profile.id,
        "contact": {
            "phone": profile.phone,
            "linkedin_url": profile.linkedin_url,
            "github_url": profile.github_url,
            "portfolio_url": profile.portfolio_url,
            "location": profile.location,
        },
        "preferences": {
            "target_roles": profile.target_roles,
            "target_industries": profile.target_industries,
            "preferred_locations": profile.preferred_locations,
            "work_mode": profile.work_mode_preference.value if profile.work_mode_preference else None,
            "experience_level": profile.experience_level.value if profile.experience_level else None,
            "job_types": profile.job_types,
            "min_salary": profile.min_salary,
            "max_salary": profile.max_salary,
            "visa_sponsorship_required": profile.visa_sponsorship_required,
            "willing_to_relocate": profile.willing_to_relocate,
            "notice_period_days": profile.notice_period_days,
        },
        "auto_apply_rules": {
            "enabled": profile.auto_apply_enabled,
            "min_match_score": profile.auto_apply_min_match_score,
            "max_daily": profile.auto_apply_max_daily,
            "require_approval_companies": profile.require_approval_companies,
            "excluded_industries": profile.excluded_industries,
            "excluded_companies": profile.excluded_companies,
        },
        "skills": profile.skills or [],
    }

@router.put("")
def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    if data.contact:
        contact = data.contact
        profile.phone = contact.phone if contact.phone is not None else profile.phone
        profile.linkedin_url = contact.linkedin_url if contact.linkedin_url is not None else profile.linkedin_url
        profile.github_url = contact.github_url if contact.github_url is not None else profile.github_url
        profile.portfolio_url = contact.portfolio_url if contact.portfolio_url is not None else profile.portfolio_url
        profile.location = contact.location if contact.location is not None else profile.location

    if data.preferences:
        prefs = data.preferences
        if prefs.target_roles is not None:
            profile.target_roles = prefs.target_roles
        if prefs.preferred_locations is not None:
            profile.preferred_locations = prefs.preferred_locations
        if prefs.min_salary is not None:
            profile.min_salary = prefs.min_salary
        if prefs.max_salary is not None:
            profile.max_salary = prefs.max_salary
        if prefs.visa_sponsorship_required is not None:
            profile.visa_sponsorship_required = prefs.visa_sponsorship_required
        if prefs.willing_to_relocate is not None:
            profile.willing_to_relocate = prefs.willing_to_relocate
        if prefs.notice_period_days is not None:
            profile.notice_period_days = prefs.notice_period_days
        if prefs.work_mode is not None:
            profile.work_mode_preference = WorkMode(prefs.work_mode)
        if prefs.experience_level is not None:
            profile.experience_level = ExperienceLevel(prefs.experience_level)

    if data.auto_apply_rules:
        rules = data.auto_apply_rules
        if rules.enabled is not None:
            profile.auto_apply_enabled = rules.enabled
        if rules.min_match_score is not None:
            profile.auto_apply_min_match_score = rules.min_match_score
        if rules.max_daily is not None:
            profile.auto_apply_max_daily = rules.max_daily
        if rules.excluded_companies is not None:
            profile.excluded_companies = rules.excluded_companies
        if rules.excluded_industries is not None:
            profile.excluded_industries = rules.excluded_industries
        if rules.require_approval_companies is not None:
            profile.require_approval_companies = rules.require_approval_companies

    db.commit()
    return {"status": "updated"}
