"""
Unit tests for LLM Tailoring and Cover Letter Generator.
"""

import pytest
from src.llm_generator import LLMGenerator, LLMGeneratorError
from src.models import (
    ATSMatchResult,
    ContactInfo,
    ExperienceEntry,
    JobRequirement,
    ResumeData,
    SeniorityLevel,
)


@pytest.fixture
def sample_resume():
    return ResumeData(
        contact=ContactInfo(name="John Doe", email="john@example.com"),
        skills=["python", "docker", "fastapi"],
        experience=[
            ExperienceEntry(
                company="Acme Corp",
                role="Backend Engineer",
                achievements=["Built distributed APIs using Python"]
            )
        ],
        years_of_experience=4.0,
        detected_seniority=SeniorityLevel.MID
    )


@pytest.fixture
def sample_job():
    return JobRequirement(
        title="Python Engineer",
        company="GlobalTech",
        required_skills=["python", "fastapi", "docker", "aws"],
        tech_keywords=["python", "docker"]
    )


@pytest.fixture
def sample_match():
    return ATSMatchResult(
        overall_score=85.0,
        skills_score=90.0,
        experience_score=80.0,
        seniority_score=100.0,
        matched_skills=["python", "fastapi", "docker"],
        missing_skills=["aws"]
    )


def test_mock_generation(sample_resume, sample_job, sample_match):
    generator = LLMGenerator(provider="mock")
    result = generator.generate_customization(sample_resume, sample_job, sample_match)

    assert "John Doe" in result.cover_letter
    assert "GlobalTech" in result.cover_letter
    assert "Python Engineer" in result.cover_letter
    assert len(result.tailored_summary) > 20
    assert "Acme Corp" in result.tailored_bullets
    assert "aws" in result.ats_keywords_to_include
    assert len(result.why_company) > 10
    assert len(result.why_role) > 10


def test_generation_null_input_raises(sample_job, sample_match):
    generator = LLMGenerator(provider="mock")
    with pytest.raises(LLMGeneratorError):
        generator.generate_customization(None, sample_job, sample_match)
