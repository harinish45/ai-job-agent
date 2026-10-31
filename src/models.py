"""
Core data models and type definitions for AI Job Agent.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any


class ApplicationStatus(str, Enum):
    """Lifecycle status of a job application."""
    PENDING = "Pending"
    APPLIED = "Applied"
    SCREENING = "Screening"
    INTERVIEW = "Interview"
    OFFER = "Offer"
    REJECTED = "Rejected"
    GHOSTED = "Ghosted"


class SeniorityLevel(str, Enum):
    """Seniority classification for candidates and job openings."""
    INTERN = "Intern"
    ENTRY = "Entry-level"
    MID = "Mid-level"
    SENIOR = "Senior"
    LEAD = "Lead/Principal"
    EXECUTIVE = "Executive"


@dataclass(frozen=True)
class ContactInfo:
    """Candidate contact information extracted from resume."""
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    location: str = ""
    portfolio: str = ""


@dataclass(frozen=True)
class EducationEntry:
    """Individual education credential."""
    institution: str
    degree: str
    field_of_study: str = ""
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None


@dataclass(frozen=True)
class ExperienceEntry:
    """Individual employment history entry."""
    company: str
    role: str
    start_date: str = ""
    end_date: str = ""
    description: str = ""
    achievements: List[str] = field(default_factory=list)
    skills_used: List[str] = field(default_factory=list)


@dataclass
class ResumeData:
    """Full structured resume data representation."""
    contact: ContactInfo = field(default_factory=ContactInfo)
    summary: str = ""
    skills: List[str] = field(default_factory=list)
    experience: List[ExperienceEntry] = field(default_factory=list)
    education: List[EducationEntry] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    years_of_experience: float = 0.0
    detected_seniority: SeniorityLevel = SeniorityLevel.ENTRY
    raw_text: str = ""


@dataclass
class JobRequirement:
    """Structured requirements extracted from a job description."""
    title: str = ""
    company: str = ""
    location: str = ""
    seniority: SeniorityLevel = SeniorityLevel.MID
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    tech_keywords: List[str] = field(default_factory=list)
    min_years_experience: float = 0.0
    is_remote: bool = False
    description: str = ""
    apply_url: str = ""


@dataclass
class ATSMatchResult:
    """ATS keyword analysis and scoring breakdown."""
    overall_score: float  # 0.0 to 100.0
    skills_score: float   # 0.0 to 100.0
    experience_score: float  # 0.0 to 100.0
    seniority_score: float   # 0.0 to 100.0
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    ats_keywords_found: List[str] = field(default_factory=list)
    ats_keywords_missing: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    calculated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class CustomizationResult:
    """AI tailored resume bullets and cover letter."""
    tailored_summary: str = ""
    tailored_bullets: Dict[str, List[str]] = field(default_factory=dict)
    cover_letter: str = ""
    ats_keywords_to_include: List[str] = field(default_factory=list)
    why_company: str = ""
    why_role: str = ""


@dataclass
class ApplicationRecord:
    """Application entity stored in database/store."""
    id: Optional[int] = None
    company: str = ""
    role: str = ""
    job_url: str = ""
    applied_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    status: ApplicationStatus = ApplicationStatus.APPLIED
    match_score: float = 0.0
    notes: str = ""
    logs: List[str] = field(default_factory=list)
