"""
End-to-end integration test for the autonomous job application agent.
"""

from pathlib import Path
from src.job_analyzer import JobAnalyzer
from src.llm_generator import LLMGenerator
from src.models import ApplicationStatus
from src.resume_parser import ResumeParser
from src.tracker import ApplicationTracker


def test_full_agent_pipeline(tmp_path):
    resume_text = """
Alex Mercer
Email: alex.mercer@example.com
Phone: (415) 555-0199
LinkedIn: linkedin.com/in/alexmercer
GitHub: github.com/alexmercer

SUMMARY
Senior Software Engineer with 7+ years of experience specializing in Python, FastAPI, and AWS cloud systems.

SKILLS
Python, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, Redis, CI/CD, Git

EXPERIENCE
Senior Python Engineer at Vertex Labs
2021 - Present
- Built real-time data processing pipelines handling 100M records daily.
- Deployed microservices using Docker, Kubernetes, and AWS ECS.

EDUCATION
Bachelor of Science in Computer Science
University of Washington
2017
"""
    job_desc = """
Job Title: Senior Cloud & Backend Engineer
Company: CloudNova
Requirements:
- 5+ years of software engineering experience.
- Deep expertise in Python, FastAPI, and PostgreSQL.
- Hands-on experience with Docker, AWS, and CI/CD.
- Excellent communication and leadership skills.
"""

    # Step 1: Parse Resume
    parser = ResumeParser()
    resume = parser.parse(resume_text)
    assert resume.contact.name == "Alex Mercer"
    assert "python" in resume.skills
    assert resume.years_of_experience == 7.0

    # Step 2: Analyze Job & Compute ATS Match
    analyzer = JobAnalyzer()
    job_req = analyzer.analyze_job(title="Senior Cloud & Backend Engineer", description=job_desc, company="CloudNova")
    match_result = analyzer.calculate_match(resume, job_req)
    assert match_result.overall_score >= 80.0
    assert "python" in match_result.matched_skills

    # Step 3: Generate Customization Materials
    generator = LLMGenerator(provider="mock")
    custom = generator.generate_customization(resume, job_req, match_result)
    assert "Alex Mercer" in custom.cover_letter
    assert "CloudNova" in custom.cover_letter

    # Step 4: Track in Application Database
    db_file = str(tmp_path / "integration_apps.db")
    tracker = ApplicationTracker(db_path=db_file)
    record = tracker.add_application(
        company=job_req.company,
        role=job_req.title,
        job_url="https://boards.greenhouse.io/cloudnova/jobs/99",
        match_score=match_result.overall_score,
        status=ApplicationStatus.APPLIED,
        notes="Automated pipeline test submission"
    )
    assert record.id is not None
    assert record.status == ApplicationStatus.APPLIED

    # Step 5: Advance Status to Interview
    tracker.update_status(record.id, ApplicationStatus.INTERVIEW, note="Interview scheduled for Thursday")
    updated = tracker.get_application(record.id)
    assert updated.status == ApplicationStatus.INTERVIEW

    # Step 6: Verify Stats
    stats = tracker.get_statistics()
    assert stats["total_applications"] == 1
    assert stats["interview_rate"] == 100.0
