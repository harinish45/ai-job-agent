"""
AI Job Agent - Database Models
Production-ready SQLAlchemy ORM models
"""
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean,
    JSON, ForeignKey, Enum, ARRAY, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.models.database import Base

class ExperienceLevel(str, enum.Enum):
    INTERN = "intern"
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    PRINCIPAL = "principal"
    EXECUTIVE = "executive"

class JobType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"

class WorkMode(str, enum.Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"

class ApplicationStatus(str, enum.Enum):
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

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relations
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    applications = relationship("JobApplication", back_populates="user")
    alerts = relationship("JobAlert", back_populates="user")
    credentials = relationship("PlatformCredential", back_populates="user")

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    # Resume Data
    resume_text = Column(Text)
    resume_file_path = Column(String(500))
    parsed_resume = Column(JSON)  # Structured resume data

    # Contact
    phone = Column(String(50))
    linkedin_url = Column(String(500))
    github_url = Column(String(500))
    portfolio_url = Column(String(500))
    location = Column(String(255))

    # Preferences
    target_roles = Column(ARRAY(String))  # ["AI Engineer", "ML Engineer"]
    target_industries = Column(ARRAY(String))
    preferred_locations = Column(ARRAY(String))
    work_mode_preference = Column(Enum(WorkMode), default=WorkMode.REMOTE)
    experience_level = Column(Enum(ExperienceLevel), default=ExperienceLevel.MID)
    job_types = Column(ARRAY(String), default=["full_time"])

    # Constraints
    min_salary = Column(Integer)  # Annual, USD
    max_salary = Column(Integer)
    visa_sponsorship_required = Column(Boolean, default=False)
    willing_to_relocate = Column(Boolean, default=False)
    notice_period_days = Column(Integer, default=30)

    # Auto-apply rules
    auto_apply_enabled = Column(Boolean, default=False)
    auto_apply_min_match_score = Column(Float, default=0.80)
    auto_apply_max_daily = Column(Integer, default=5)
    require_approval_companies = Column(ARRAY(String))  # Company names
    excluded_industries = Column(ARRAY(String))
    excluded_companies = Column(ARRAY(String))

    # Skills & Keywords
    skills = Column(ARRAY(String))
    strengths = Column(ARRAY(String))
    gaps = Column(ARRAY(String))
    transferable_skills = Column(ARRAY(String))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")

class PlatformCredential(Base):
    __tablename__ = "platform_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    platform = Column(String(100), nullable=False)  # linkedin, indeed, etc.
    username_encrypted = Column(Text)
    password_encrypted = Column(Text)
    cookies_encrypted = Column(Text)  # Session cookies for persistent login
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="credentials")

    __table_args__ = (Index("idx_platform_user", "user_id", "platform"),)

class JobListing(Base):
    __tablename__ = "job_listings"

    id = Column(Integer, primary_key=True, index=True)

    # Source
    source_platform = Column(String(100), nullable=False, index=True)  # linkedin, indeed, company_career_page
    source_url = Column(String(1000), unique=True, index=True)
    external_id = Column(String(255), index=True)  # Platform-specific job ID

    # Job Details
    title = Column(String(500), nullable=False)
    company = Column(String(255), nullable=False, index=True)
    company_size = Column(String(50))
    company_industry = Column(String(100))
    location = Column(String(255))
    work_mode = Column(Enum(WorkMode))
    job_type = Column(Enum(JobType))
    experience_level = Column(Enum(ExperienceLevel))

    # Description & Requirements
    description = Column(Text)
    requirements = Column(ARRAY(String))
    responsibilities = Column(ARRAY(String))
    skills_required = Column(ARRAY(String))

    # Compensation
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    salary_currency = Column(String(10), default="USD")
    salary_period = Column(String(20), default="yearly")

    # Application
    apply_url = Column(String(1000))
    apply_method = Column(String(50))  # direct_link, easy_apply, email, form
    application_deadline = Column(DateTime)

    # AI Analysis
    is_ai_role = Column(Boolean, default=False)
    ai_role_category = Column(String(100))  # prompt_engineer, ai_ops, etc.
    is_scam_flagged = Column(Boolean, default=False)
    scam_reason = Column(String(500))

    # Metadata
    posted_at = Column(DateTime)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(Integer, ForeignKey("job_listings.id"), nullable=True)

    # Relations
    match_scores = relationship("JobMatchScore", back_populates="job")
    applications = relationship("JobApplication", back_populates="job")

    __table_args__ = (
        Index("idx_job_search", "title", "company"),
        Index("idx_job_active", "is_active", "discovered_at"),
    )

class JobMatchScore(Base):
    __tablename__ = "job_match_scores"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_listings.id"))
    user_id = Column(Integer, ForeignKey("users.id"))

    # Scoring (0.0 - 1.0)
    overall_score = Column(Float, nullable=False, index=True)
    skills_match = Column(Float)
    experience_match = Column(Float)
    location_match = Column(Float)
    salary_match = Column(Float)
    role_match = Column(Float)
    culture_match = Column(Float)

    # Analysis
    matching_skills = Column(ARRAY(String))
    missing_skills = Column(ARRAY(String))
    transferrable_skills_applicable = Column(ARRAY(String))
    gap_analysis = Column(Text)
    recommendation = Column(Text)

    # Customization
    tailored_resume_bullets = Column(JSON)  # {original: str, tailored: str}
    generated_cover_letter = Column(Text)
    ats_keywords = Column(ARRAY(String))
    why_company_answer = Column(Text)
    why_role_answer = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship("JobListing", back_populates="match_scores")

    __table_args__ = (Index("idx_match_user_score", "user_id", "overall_score"),)

class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("job_listings.id"))

    # Status Tracking
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.NEW)
    status_history = Column(JSON, default=list)  # [{status, timestamp, note}]

    # Application Details
    applied_at = Column(DateTime)
    auto_applied = Column(Boolean, default=False)
    required_approval = Column(Boolean, default=False)
    approved_at = Column(DateTime)
    approved_by = Column(String(50))  # user or system

    # Form Data
    form_data = Column(JSON)  # Submitted form fields
    uploaded_resume_path = Column(String(500))
    cover_letter_path = Column(String(500))

    # Screening Answers
    screening_answers = Column(JSON)  # {question: answer}

    # Communication
    recruiter_name = Column(String(255))
    recruiter_email = Column(String(255))
    recruiter_phone = Column(String(50))
    last_contact_date = Column(DateTime)
    next_follow_up_date = Column(DateTime)

    # Interview Tracking
    interview_rounds = Column(JSON, default=list)  # [{round, date, type, notes}]
    offer_details = Column(JSON)  # {salary, benefits, deadline}

    # Logs
    application_logs = Column(JSON, default=list)  # Detailed action logs
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="applications")
    job = relationship("JobListing", back_populates="applications")

    __table_args__ = (
        Index("idx_app_user_status", "user_id", "status"),
        Index("idx_app_dates", "applied_at", "next_follow_up_date"),
    )

class JobAlert(Base):
    __tablename__ = "job_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    alert_type = Column(String(50))  # instant, daily_summary, weekly_report
    title = Column(String(255))
    content = Column(Text)
    jobs_referenced = Column(ARRAY(Integer))  # Job IDs
    is_read = Column(Boolean, default=False)
    sent_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="alerts")

class ApplicationLog(Base):
    __tablename__ = "application_logs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("job_applications.id"))
    action = Column(String(100), nullable=False)  # form_fill, submit, captcha_detected, error
    details = Column(JSON)
    screenshot_path = Column(String(500))
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean)
    error_message = Column(Text)

class LearningFeedback(Base):
    __tablename__ = "learning_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    application_id = Column(Integer, ForeignKey("job_applications.id"))

    # Outcome
    outcome = Column(String(50))  # accepted, rejected, ghosted, interview, offer
    feedback_text = Column(Text)

    # What worked / didn't
    successful_elements = Column(ARRAY(String))
    failed_elements = Column(ARRAY(String))

    # Model learning
    match_score_at_apply = Column(Float)
    resume_version = Column(String(50))
    cover_letter_version = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)
