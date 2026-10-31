"""
Unit tests for Resume Parser module.
"""

import pytest
from src.models import SeniorityLevel
from src.resume_parser import ResumeParser, ResumeParserError


SAMPLE_RESUME_TEXT = """
Jane Doe
Email: jane.doe@example.com
Phone: (555) 987-6543
LinkedIn: linkedin.com/in/janedoe
GitHub: github.com/janedoe

SUMMARY
Lead Python Architect with 8+ years of experience building distributed microservices and ML applications.

SKILLS
Programming: Python, TypeScript, SQL, Bash
Frameworks: FastAPI, Django, React
AI/ML: PyTorch, TensorFlow, LangChain, OpenAI
Cloud & DevOps: AWS, Docker, Kubernetes, Terraform

EXPERIENCE
Lead Architect at TechCorp
- Architected enterprise cloud infrastructure on AWS and Kubernetes.
- Optimized REST API throughput by 40% using FastAPI and Redis.

Software Engineer at CloudStart
- Developed asynchronous task queues using Python and PostgreSQL.

EDUCATION
Master of Science in Computer Science
Stanford University
2016
"""


def test_parse_valid_resume():
    parser = ResumeParser()
    resume = parser.parse(SAMPLE_RESUME_TEXT)

    assert resume.contact.name == "Jane Doe"
    assert resume.contact.email == "jane.doe@example.com"
    assert resume.contact.phone == "(555) 987-6543"
    assert "linkedin.com/in/janedoe" in resume.contact.linkedin
    assert "github.com/janedoe" in resume.contact.github
    assert resume.years_of_experience == 8.0
    assert resume.detected_seniority == SeniorityLevel.SENIOR


def test_extract_skills():
    parser = ResumeParser()
    skills = parser.extract_skills(SAMPLE_RESUME_TEXT)

    assert "python" in skills
    assert "fastapi" in skills
    assert "aws" in skills
    assert "docker" in skills
    assert "pytorch" in skills


def test_extract_education():
    parser = ResumeParser()
    education = parser.extract_education(SAMPLE_RESUME_TEXT)

    assert len(education) >= 1
    assert education[0].degree == "Master of Science"
    assert education[0].graduation_year == 2016


def test_extract_experience():
    parser = ResumeParser()
    experience = parser.extract_experience(SAMPLE_RESUME_TEXT)

    assert len(experience) >= 2
    roles = [e.role for e in experience]
    assert any("Lead Architect" in r for r in roles)
    assert any("Software Engineer" in r for r in roles)


def test_parse_empty_resume_raises_error():
    parser = ResumeParser()
    with pytest.raises(ResumeParserError):
        parser.parse("   ")


def test_parse_missing_file_raises_error():
    parser = ResumeParser()
    with pytest.raises(FileNotFoundError):
        parser.parse_file("non_existent_resume_file.txt")
