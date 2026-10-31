"""
Job Description Analyzer and ATS Matcher.
Extracts keywords, required skills, seniority, and computes 0-100% ATS match scores.
"""

import logging
import re
from typing import Dict, List, Set, Tuple

from src.models import (
    ATSMatchResult,
    JobRequirement,
    ResumeData,
    SeniorityLevel,
)

logger = logging.getLogger(__name__)


class JobAnalyzerError(Exception):
    """Raised when job description analysis fails."""
    pass


class JobAnalyzer:
    """Analyzer for job descriptions and ATS compliance evaluation."""

    COMMON_TECH_KEYWORDS: Set[str] = {
        "python", "javascript", "typescript", "java", "c++", "c#", "go",
        "rust", "ruby", "sql", "nosql", "postgresql", "mysql", "mongodb",
        "redis", "react", "next.js", "vue", "angular", "node.js", "fastapi",
        "django", "flask", "docker", "kubernetes", "aws", "azure", "gcp",
        "terraform", "ci/cd", "git", "rest", "graphql", "microservices",
        "machine learning", "deep learning", "nlp", "llm", "genai", "pytorch",
        "tensorflow", "scikit-learn", "spark", "kafka", "airflow", "pandas",
        "numpy", "agile", "scrum", "tdd", "system design", "linux"
    }

    SENIORITY_INDICATORS: Dict[SeniorityLevel, List[str]] = {
        SeniorityLevel.INTERN: ["intern", "internship", "co-op", "trainee"],
        SeniorityLevel.ENTRY: ["junior", "entry-level", "associate", "jr.", "grad", "graduate"],
        SeniorityLevel.MID: ["mid-level", "intermediate", "software engineer", "developer"],
        SeniorityLevel.SENIOR: ["senior", "sr.", "staff", "principal", "architect"],
        SeniorityLevel.LEAD: ["lead", "tech lead", "engineering manager", "head of"],
        SeniorityLevel.EXECUTIVE: ["director", "vp", "chief", "cto", "cio"]
    }

    def analyze_job(self, title: str, description: str, company: str = "") -> JobRequirement:
        """Parse raw job description into structured requirements."""
        if not description or not description.strip():
            raise JobAnalyzerError("Job description cannot be empty.")

        norm_desc = description.lower()
        seniority = self.extract_seniority(title, norm_desc)
        skills_req, skills_pref = self.extract_skills(norm_desc)
        tech_keywords = self.extract_tech_keywords(norm_desc)
        min_years = self.extract_experience_years(norm_desc)
        is_remote = any(term in norm_desc for term in ["remote", "work from home", "anywhere in the us"])

        return JobRequirement(
            title=title,
            company=company,
            seniority=seniority,
            required_skills=skills_req,
            preferred_skills=skills_pref,
            tech_keywords=tech_keywords,
            min_years_experience=min_years,
            is_remote=is_remote,
            description=description
        )

    def calculate_match(self, resume: ResumeData, job: JobRequirement) -> ATSMatchResult:
        """Calculate weighted ATS match percentage (0-100%) and recommendations."""
        if not resume or not job:
            raise JobAnalyzerError("Resume and JobRequirement cannot be None.")

        resume_skills_lower = {s.lower() for s in resume.skills}
        req_skills_lower = {s.lower() for s in job.required_skills}

        # 1. Skills Matching Score (0 - 100)
        skills_score, matched_skills, missing_skills = self._score_skills(
            resume_skills_lower, req_skills_lower
        )

        # 2. Keywords Overlap (0 - 100)
        kw_score, kw_found, kw_missing = self._score_keywords(
            resume.raw_text.lower(), job.tech_keywords
        )

        # 3. Experience & Seniority Scores (0 - 100)
        exp_score = self._score_experience(resume.years_of_experience, job.min_years_experience)
        sen_score = self._score_seniority(resume.detected_seniority, job.seniority)

        # Weighted calculation
        overall = (
            (skills_score * 0.40) +
            (kw_score * 0.25) +
            (exp_score * 0.20) +
            (sen_score * 0.15)
        )
        overall = round(min(100.0, max(0.0, overall)), 1)

        recommendations = self._generate_recommendations(
            overall, missing_skills, kw_missing, exp_score
        )

        logger.info("ATS evaluation completed. Overall score: %.1f%%", overall)
        return ATSMatchResult(
            overall_score=overall,
            skills_score=round(skills_score, 1),
            experience_score=round(exp_score, 1),
            seniority_score=round(sen_score, 1),
            matched_skills=sorted(list(matched_skills)),
            missing_skills=sorted(list(missing_skills)),
            ats_keywords_found=sorted(list(kw_found)),
            ats_keywords_missing=sorted(list(kw_missing)),
            recommendations=recommendations,
        )

    def extract_seniority(self, title: str, description: str) -> SeniorityLevel:
        """Infer required seniority level from job title and description."""
        combined = f"{title.lower()} {description.lower()[:300]}"
        for level in [SeniorityLevel.EXECUTIVE, SeniorityLevel.LEAD, SeniorityLevel.SENIOR,
                      SeniorityLevel.INTERN, SeniorityLevel.ENTRY]:
            for indicator in self.SENIORITY_INDICATORS[level]:
                if re.search(r"\b" + re.escape(indicator) + r"\b", combined):
                    return level
        return SeniorityLevel.MID

    def extract_tech_keywords(self, text: str) -> List[str]:
        """Extract recognized tech and domain keywords from text."""
        text_lower = text.lower()
        found: Set[str] = set()
        for kw in self.COMMON_TECH_KEYWORDS:
            if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                found.add(kw)
        return sorted(list(found))

    def extract_skills(self, text: str) -> Tuple[List[str], List[str]]:
        """Separate required skills from preferred/nice-to-have skills."""
        req_skills: Set[str] = set()
        pref_skills: Set[str] = set()

        # Split text into sections if possible
        sections = re.split(r"(?:requirements|qualifications|preferred|nice to have)", text, flags=re.IGNORECASE)
        for kw in self.COMMON_TECH_KEYWORDS:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if len(sections) > 1 and re.search(pattern, sections[1]):
                req_skills.add(kw)
            elif re.search(pattern, text):
                req_skills.add(kw)

        if len(sections) > 2:
            for kw in self.COMMON_TECH_KEYWORDS:
                if re.search(r"\b" + re.escape(kw) + r"\b", sections[2]):
                    pref_skills.add(kw)

        return sorted(list(req_skills)), sorted(list(pref_skills))

    def extract_experience_years(self, text: str) -> float:
        """Extract minimum years of required professional experience."""
        matches = re.findall(r"(\d+)(?:\+|-|\s+to\s+\d+)?\s*years?(?:\s+of)?\s+experience", text, re.IGNORECASE)
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                return 0.0
        return 0.0

    def _score_skills(self, candidate_skills: Set[str], required_skills: Set[str]) -> Tuple[float, Set[str], Set[str]]:
        """Calculate skill match ratio."""
        if not required_skills:
            return 100.0, candidate_skills, set()
        matched = candidate_skills & required_skills
        missing = required_skills - candidate_skills
        score = (len(matched) / len(required_skills)) * 100.0
        return min(100.0, score), matched, missing

    def _score_keywords(self, resume_text: str, tech_keywords: List[str]) -> Tuple[float, Set[str], Set[str]]:
        """Check presence of tech keywords in raw resume text."""
        if not tech_keywords:
            return 100.0, set(), set()
        found: Set[str] = set()
        missing: Set[str] = set()
        for kw in tech_keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", resume_text):
                found.add(kw)
            else:
                missing.add(kw)
        score = (len(found) / len(tech_keywords)) * 100.0
        return min(100.0, score), found, missing

    def _score_experience(self, candidate_years: float, required_years: float) -> float:
        """Score candidate years of experience vs required minimum."""
        if required_years <= 0.0:
            return 100.0
        if candidate_years >= required_years:
            return 100.0
        gap = required_years - candidate_years
        return max(20.0, 100.0 - (gap * 20.0))

    def _score_seniority(self, candidate_level: SeniorityLevel, required_level: SeniorityLevel) -> float:
        """Score alignment of seniority levels."""
        ranks = {
            SeniorityLevel.INTERN: 1,
            SeniorityLevel.ENTRY: 2,
            SeniorityLevel.MID: 3,
            SeniorityLevel.SENIOR: 4,
            SeniorityLevel.LEAD: 5,
            SeniorityLevel.EXECUTIVE: 6,
        }
        diff = ranks.get(candidate_level, 3) - ranks.get(required_level, 3)
        if diff >= 0:
            return 100.0
        elif diff == -1:
            return 80.0
        elif diff == -2:
            return 60.0
        return 40.0

    def _generate_recommendations(
        self,
        overall: float,
        missing_skills: Set[str],
        missing_keywords: Set[str],
        exp_score: float
    ) -> List[str]:
        """Generate human-actionable resume improvement tips."""
        tips: List[str] = []
        if overall >= 85.0:
            tips.append("Excellent ATS alignment. Ready for direct application.")
        elif overall >= 70.0:
            tips.append("Good match! Tailor resume bullets with specific missing keywords to boost score.")
        else:
            tips.append("Moderate match. Review missing core competencies before applying.")

        if missing_skills:
            sample_missing = ", ".join(list(missing_skills)[:4])
            tips.append(f"Incorporate missing core skills: {sample_missing}")

        if missing_keywords:
            sample_kw = ", ".join(list(missing_keywords)[:4])
            tips.append(f"Add industry tech keywords into project descriptions: {sample_kw}")

        if exp_score < 70.0:
            tips.append("Highlight high-impact projects or leadership to offset experience gap.")

        return tips
