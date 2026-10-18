"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class WorkMode(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"

class ExperienceLevel(str, Enum):
    INTERN = "intern"
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    PRINCIPAL = "principal"
    EXECUTIVE = "executive"

class JobType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"

class ApplicationStatus(str, Enum):
    NEW = "new"
    PENDING_APPROVAL = "pending_approval"
    AUTO_APPLYING = "auto_applying"
    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    GHOSTED = "ghosted"
    WITHDRAWN = "withdrawn"
    SAVED = "saved"
    EXPIRED = "expired"

# ==================== AUTH ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int

# ==================== PROFILE ====================

class ContactInfo(BaseModel):
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    location: Optional[str] = None

class JobPreferences(BaseModel):
    target_roles: Optional[List[str]] = None
    target_industries: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    work_mode: Optional[WorkMode] = None
    experience_level: Optional[ExperienceLevel] = None
    job_types: Optional[List[str]] = None
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    visa_sponsorship_required: Optional[bool] = None
    willing_to_relocate: Optional[bool] = None
    notice_period_days: Optional[int] = None

class AutoApplyRules(BaseModel):
    enabled: Optional[bool] = None
    min_match_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_daily: Optional[int] = Field(None, ge=1, le=50)
    require_approval_companies: Optional[List[str]] = None
    excluded_industries: Optional[List[str]] = None
    excluded_companies: Optional[List[str]] = None

class ProfileUpdate(BaseModel):
    contact: Optional[ContactInfo] = None
    preferences: Optional[JobPreferences] = None
    auto_apply_rules: Optional[AutoApplyRules] = None

class ProfileResponse(BaseModel):
    id: int
    contact: ContactInfo
    preferences: JobPreferences
    auto_apply_rules: AutoApplyRules
    skills: List[str]

    class Config:
        from_attributes = True

# ==================== RESUME ====================

class ResumeAnalysisResponse(BaseModel):
    strengths: List[str]
    gaps: List[str]
    transferable_skills: List[str]
    suggestions: List[Dict[str, Any]]
    is_ai_professional: bool
    ai_role_categories: List[str]

class ResumeUploadResponse(BaseModel):
    status: str
    parsed_data: Dict[str, Any]
    suggestions: List[Dict[str, Any]]

# ==================== JOBS ====================

class JobListingResponse(BaseModel):
    id: int
    title: str
    company: str
    location: Optional[str]
    work_mode: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    source_platform: str
    source_url: Optional[str]
    apply_url: Optional[str]
    is_ai_role: bool
    ai_role_category: Optional[str]
    posted_at: Optional[datetime]
    match_score: Optional[float]
    is_strong_match: bool

class JobListResponse(BaseModel):
    jobs: List[JobListingResponse]
    total: int

class MatchScoreResponse(BaseModel):
    overall_score: float
    skills_match: float
    experience_match: float
    role_match: float
    location_match: float
    salary_match: float
    culture_match: float
    matching_skills: List[str]
    missing_skills: List[str]
    transferable_skills_applicable: List[str]
    gap_analysis: str
    recommendation: str
    is_strong_match: bool

class CustomizationResponse(BaseModel):
    tailored_resume_bullets: Dict[str, str]
    generated_cover_letter: str
    screening_answers: Dict[str, str]
    ats_keywords: List[str]
    why_company: str
    why_role: str

class JobMatchDetailResponse(BaseModel):
    match: MatchScoreResponse
    customization: CustomizationResponse

# ==================== APPLICATIONS ====================

class ApplicationCreate(BaseModel):
    auto_apply: bool = False

class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus
    note: Optional[str] = None

class ApplicationResponse(BaseModel):
    id: int
    job_title: str
    company: str
    status: str
    applied_at: Optional[datetime]
    auto_applied: bool
    next_follow_up: Optional[datetime]
    source_platform: Optional[str]

class ApplicationListResponse(BaseModel):
    applications: List[ApplicationResponse]

# ==================== DASHBOARD ====================

class PlatformStat(BaseModel):
    platform: str
    count: int

class DashboardStatsResponse(BaseModel):
    total_applied: int
    interviews: int
    offers: int
    rejections: int
    ghosted: int
    interview_rate: float
    offer_rate: float
    platform_breakdown: List[PlatformStat]

# ==================== ALERTS ====================

class AlertResponse(BaseModel):
    id: int
    type: str
    title: str
    content: Optional[str]
    is_read: bool
    sent_at: datetime

class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]

# ==================== SEARCH ====================

class SearchTriggerResponse(BaseModel):
    task_id: str
    status: str

# ==================== CREDENTIALS ====================

class CredentialCreate(BaseModel):
    platform: str
    username: str
    password: str

class CredentialResponse(BaseModel):
    id: int
    platform: str
    is_active: bool
    last_used: Optional[datetime]
