"""
Unit tests for Job Description Analyzer and ATS Matcher.
"""

import pytest
from src.job_analyzer import JobAnalyzer, JobAnalyzerError
from src.models import ResumeData, ContactInfo, SeniorityLevel


SAMPLE_JOB_DESC = """
Title: Senior Backend Developer
Company: InnovateTech
Location: Remote

We are seeking a Senior Backend Developer with 5+ years of experience.
Requirements:
- Strong experience in Python, FastAPI, and PostgreSQL.
- Hands-on skills in Docker, AWS, and Git.
- Background in building microservices and RESTful APIs.

Preferred:
- Kubernetes and Redis experience.
"""


def test_analyze_job():
    analyzer = JobAnalyzer()
    req = analyzer.analyze_job(
        title="Senior Backend Developer",
        description=SAMPLE_JOB_DESC,
        company="InnovateTech"
    )

    assert req.title == "Senior Backend Developer"
    assert req.company == "InnovateTech"
    assert req.seniority == SeniorityLevel.SENIOR
    assert req.min_years_experience == 5.0
    assert req.is_remote is True
    assert "python" in req.tech_keywords
    assert "docker" in req.tech_keywords


def test_calculate_match_high():
    analyzer = JobAnalyzer()
    req = analyzer.analyze_job("Senior Developer", SAMPLE_JOB_DESC, "InnovateTech")

    resume = ResumeData(
        contact=ContactInfo(name="Alice Engineer", email="alice@test.com"),
        skills=["python", "fastapi", "postgresql", "docker", "aws", "git", "redis"],
        years_of_experience=6.0,
        detected_seniority=SeniorityLevel.SENIOR,
        raw_text="Alice Engineer with Python, FastAPI, Docker, AWS, PostgreSQL, Redis experience."
    )

    result = analyzer.calculate_match(resume, req)

    assert result.overall_score >= 80.0
    assert "python" in result.matched_skills
    assert "docker" in result.matched_skills
    assert len(result.recommendations) >= 1


def test_calculate_match_gaps():
    analyzer = JobAnalyzer()
    req = analyzer.analyze_job("Senior Developer", SAMPLE_JOB_DESC, "InnovateTech")

    resume = ResumeData(
        contact=ContactInfo(name="Bob Junior", email="bob@test.com"),
        skills=["javascript", "react"],
        years_of_experience=1.0,
        detected_seniority=SeniorityLevel.ENTRY,
        raw_text="Bob Junior front-end developer with Javascript and React."
    )

    result = analyzer.calculate_match(resume, req)

    assert result.overall_score < 60.0
    assert "python" in result.missing_skills
    assert any("missing" in rec.lower() for rec in result.recommendations)


def test_empty_job_description_raises():
    analyzer = JobAnalyzer()
    with pytest.raises(JobAnalyzerError):
        analyzer.analyze_job("Role", "")
