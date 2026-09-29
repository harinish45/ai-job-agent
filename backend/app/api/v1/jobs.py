"""
Job listing and matching API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.models.database import get_db
from app.models.models import User, UserProfile, JobListing, JobMatchScore
from app.core.security import get_current_user
from app.services.job_matcher import JobMatcher
from app.schemas.schemas import (
    JobListResponse, JobListingResponse,
    JobMatchDetailResponse, SearchTriggerResponse
)
from app.core.celery_app import celery_app
from app.services.job_search import daily_job_search

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.get("", response_model=JobListResponse)
def get_jobs(
    status: Optional[str] = None,
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0),
    is_ai_role: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(JobListing).filter(JobListing.is_active == True)

    if is_ai_role is not None:
        query = query.filter(JobListing.is_ai_role == is_ai_role)

    jobs = query.order_by(JobListing.discovered_at.desc()).offset(offset).limit(limit).all()

    result = []
    for job in jobs:
        match = db.query(JobMatchScore).filter(
            JobMatchScore.job_id == job.id,
            JobMatchScore.user_id == current_user.id
        ).first()

        result.append({
            "id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "work_mode": job.work_mode.value if job.work_mode else None,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "source_platform": job.source_platform,
            "source_url": job.source_url,
            "apply_url": job.apply_url,
            "is_ai_role": job.is_ai_role,
            "ai_role_category": job.ai_role_category,
            "posted_at": job.posted_at,
            "match_score": match.overall_score if match else None,
            "is_strong_match": match.is_strong_match if match else False,
        })

    if min_score:
        result = [j for j in result if j.match_score is not None and j.match_score >= min_score]

    return {"jobs": result, "total": len(result)}

@router.post("/{job_id}/match", response_model=JobMatchDetailResponse)
async def calculate_match(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile or not profile.parsed_resume:
        raise HTTPException(status_code=400, detail="Upload resume first")

    profile_dict = {
        "name": profile.parsed_resume.get("name", ""),
        "title": profile.parsed_resume.get("title", ""),
        "summary": profile.parsed_resume.get("summary", ""),
        "skills": profile.skills or [],
        "experience": profile.parsed_resume.get("experience", []),
        "years_of_experience": profile.years_of_experience or 0,
        "target_roles": profile.target_roles or [],
        "location": profile.location or "",
        "preferred_locations": profile.preferred_locations or [],
        "work_mode_preference": profile.work_mode_preference.value if profile.work_mode_preference else "remote",
        "min_salary": profile.min_salary,
        "max_salary": profile.max_salary,
        "transferable_skills": profile.transferable_skills or [],
    }

    job_dict = {
        "title": job.title,
        "company": job.company,
        "description": job.description or "",
        "skills_required": job.skills_required or [],
        "experience_level": job.experience_level.value if job.experience_level else None,
        "location": job.location or "",
        "work_mode": job.work_mode.value if job.work_mode else "remote",
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
    }

    matcher = JobMatcher()
    match_data = await matcher.calculate_match(profile_dict, job_dict)
    customization = await matcher.generate_customization(profile_dict, job_dict, match_data)

    existing = db.query(JobMatchScore).filter(
        JobMatchScore.job_id == job_id,
        JobMatchScore.user_id == current_user.id
    ).first()

    if existing:
        existing.overall_score = match_data["overall_score"]
        existing.skills_match = match_data["skills_match"]
        existing.experience_match = match_data["experience_match"]
        existing.role_match = match_data["role_match"]
        existing.location_match = match_data["location_match"]
        existing.salary_match = match_data["salary_match"]
        existing.culture_match = match_data["culture_match"]
        existing.matching_skills = match_data["matching_skills"]
        existing.missing_skills = match_data["missing_skills"]
        existing.transferable_skills_applicable = match_data["transferable_skills_applicable"]
        existing.gap_analysis = match_data["gap_analysis"]
        existing.recommendation = match_data["recommendation"]
        existing.generated_cover_letter = customization["generated_cover_letter"]
        existing.ats_keywords = customization["ats_keywords"]
        existing.tailored_resume_bullets = customization["tailored_resume_bullets"]
    else:
        match_score = JobMatchScore(
            job_id=job_id,
            user_id=current_user.id,
            overall_score=match_data["overall_score"],
            skills_match=match_data["skills_match"],
            experience_match=match_data["experience_match"],
            role_match=match_data["role_match"],
            location_match=match_data["location_match"],
            salary_match=match_data["salary_match"],
            culture_match=match_data["culture_match"],
            matching_skills=match_data["matching_skills"],
            missing_skills=match_data["missing_skills"],
            transferable_skills_applicable=match_data["transferable_skills_applicable"],
            gap_analysis=match_data["gap_analysis"],
            recommendation=match_data["recommendation"],
            generated_cover_letter=customization["generated_cover_letter"],
            ats_keywords=customization["ats_keywords"],
            tailored_resume_bullets=customization["tailored_resume_bullets"],
        )
        db.add(match_score)

    db.commit()

    return {
        "match": match_data,
        "customization": customization
    }

@router.post("/search/trigger", response_model=SearchTriggerResponse)
def trigger_search(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = daily_job_search.delay(current_user.id)
    return {"task_id": task.id, "status": "queued"}
