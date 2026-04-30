"""
Resume API routes.
"""
import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.models import User, UserProfile
from app.core.security import get_current_user
from app.services.resume_parser import ResumeParser
from app.schemas.schemas import ResumeUploadResponse, ResumeAnalysisResponse
import asyncio

router = APIRouter(prefix="/resume", tags=["resume"])

@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    upload_dir = "./uploads/resumes"
    os.makedirs(upload_dir, exist_ok=True)

    file_path = f"{upload_dir}/{current_user.id}_{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = ""
    if file.filename.endswith('.pdf'):
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    elif file.filename.endswith('.docx'):
        import docx
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
    else:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()

    parser = ResumeParser()
    parsed = await parser.parse_resume(text, file.filename.split('.')[-1])

    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if profile:
        profile.resume_text = text
        profile.resume_file_path = file_path
        profile.parsed_resume = parsed
        profile.skills = parsed.get("skills", [])
        profile.strengths = parsed.get("analysis", {}).get("strengths", [])
        profile.gaps = parsed.get("analysis", {}).get("gaps", [])
        profile.transferable_skills = parsed.get("analysis", {}).get("transferable_skills", [])
        profile.years_of_experience = parsed.get("years_of_experience", 0)
        profile.industries = parsed.get("industries", [])
        profile.target_roles = parsed.get("target_roles", [])

        contact = parsed.get("contact", {})
        profile.phone = contact.get("phone", "")
        profile.linkedin_url = contact.get("linkedin", "")
        profile.github_url = contact.get("github", "")

    db.commit()

    return {
        "status": "success",
        "parsed_data": parsed,
        "suggestions": parsed.get("suggestions", [])
    }

@router.get("/analysis", response_model=ResumeAnalysisResponse)
def get_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile or not profile.parsed_resume:
        raise HTTPException(status_code=404, detail="No resume uploaded")

    return {
        "strengths": profile.strengths or [],
        "gaps": profile.gaps or [],
        "transferable_skills": profile.transferable_skills or [],
        "suggestions": profile.parsed_resume.get("suggestions", []),
        "is_ai_professional": profile.parsed_resume.get("is_ai_professional", False),
        "ai_role_categories": profile.parsed_resume.get("ai_role_categories", [])
    }
