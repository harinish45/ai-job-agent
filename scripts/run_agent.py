#!/usr/bin/env python3
"""
AI Job Application Agent - CLI Entry Point.
Autonomous ATS evaluation, resume tailoring, cover letter generation, and application pipeline.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.auto_apply import AutoApplyEngine
from src.job_analyzer import JobAnalyzer
from src.llm_generator import LLMGenerator
from src.models import ApplicationStatus
from src.resume_parser import ResumeParser
from src.tracker import ApplicationTracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ai_job_agent")


def handle_parse(args: argparse.Namespace) -> None:
    """Parse resume and print structured data."""
    parser = ResumeParser()
    resume = parser.parse_file(args.resume)
    data = {
        "candidate": resume.contact.name,
        "email": resume.contact.email,
        "phone": resume.contact.phone,
        "seniority": resume.detected_seniority.value,
        "years_experience": resume.years_of_experience,
        "skills": resume.skills,
        "education": [e.degree for e in resume.education],
        "experience": [f"{e.role} at {e.company}" for e in resume.experience]
    }
    print(json.dumps(data, indent=2))


def handle_analyze(args: argparse.Namespace) -> None:
    """Analyze job description text and output requirements."""
    desc = Path(args.job).read_text(encoding="utf-8") if os.path.exists(args.job) else args.job
    analyzer = JobAnalyzer()
    job_req = analyzer.analyze_job(title=args.title or "Position", description=desc, company=args.company or "")
    data = {
        "title": job_req.title,
        "company": job_req.company,
        "seniority": job_req.seniority.value,
        "required_skills": job_req.required_skills,
        "tech_keywords": job_req.tech_keywords,
        "min_years_experience": job_req.min_years_experience,
        "is_remote": job_req.is_remote
    }
    print(json.dumps(data, indent=2))


def handle_match(args: argparse.Namespace) -> None:
    """Evaluate ATS match between a resume and a job description."""
    parser = ResumeParser()
    resume = parser.parse_file(args.resume)

    desc = Path(args.job).read_text(encoding="utf-8") if os.path.exists(args.job) else args.job
    analyzer = JobAnalyzer()
    job_req = analyzer.analyze_job(title=args.title or "Position", description=desc, company=args.company or "")

    result = analyzer.calculate_match(resume, job_req)
    print("\n" + "=" * 50)
    print(f"🎯 ATS Match Score: {result.overall_score}%")
    print("=" * 50)
    print(f"Skills Score:     {result.skills_score}%")
    print(f"Experience Score: {result.experience_score}%")
    print(f"Seniority Score:  {result.seniority_score}%")
    print(f"Matched Skills:   {', '.join(result.matched_skills) or 'None'}")
    print(f"Missing Skills:   {', '.join(result.missing_skills) or 'None'}")
    print("\nRecommendations:")
    for rec in result.recommendations:
        print(f" • {rec}")
    print("=" * 50 + "\n")


def handle_tailor(args: argparse.Namespace) -> None:
    """Generate tailored resume bullets and cover letter."""
    parser = ResumeParser()
    resume = parser.parse_file(args.resume)

    desc = Path(args.job).read_text(encoding="utf-8") if os.path.exists(args.job) else args.job
    analyzer = JobAnalyzer()
    job_req = analyzer.analyze_job(title=args.title or "Engineer", description=desc, company=args.company or "Company")
    match_result = analyzer.calculate_match(resume, job_req)

    generator = LLMGenerator(provider=args.provider)
    custom = generator.generate_customization(resume, job_req, match_result)

    print("\n" + "=" * 50)
    print("📝 TAILORED SUMMARY:")
    print(custom.tailored_summary)
    print("\n✉️ COVER LETTER:")
    print(custom.cover_letter)
    print("=" * 50 + "\n")


def handle_track(args: argparse.Namespace) -> None:
    """Query, filter, or view application metrics."""
    tracker = ApplicationTracker(db_path=args.db)
    if args.stats:
        stats = tracker.get_statistics()
        print(json.dumps(stats, indent=2))
        return

    if args.update_id and args.status:
        updated = tracker.update_status(args.update_id, ApplicationStatus(args.status), note=args.note)
        print(f"Updated application #{args.update_id}: {updated}")
        return

    status_filter = ApplicationStatus(args.filter_status) if args.filter_status else None
    apps = tracker.list_applications(status=status_filter, search=args.search)
    print(f"\nFound {len(apps)} application record(s):")
    for app in apps:
        print(f"[{app.id}] {app.applied_at} | {app.company} - {app.role} | Status: {app.status.value} | Match: {app.match_score}%")


def handle_batch(args: argparse.Namespace) -> None:
    """Run full autonomous pipeline: parse -> match -> tailor -> apply -> track."""
    print("🚀 Starting autonomous job agent batch pipeline...")
    parser = ResumeParser()
    resume = parser.parse_file(args.resume)

    desc = Path(args.job).read_text(encoding="utf-8") if os.path.exists(args.job) else args.job
    analyzer = JobAnalyzer()
    job_req = analyzer.analyze_job(title=args.title, description=desc, company=args.company)

    match_result = analyzer.calculate_match(resume, job_req)
    print(f"📊 Evaluated ATS match: {match_result.overall_score}%")

    if match_result.overall_score < args.min_score:
        print(f"⚠️ Match score {match_result.overall_score}% is below threshold {args.min_score}%. Skipping apply.")
        return

    generator = LLMGenerator(provider=args.provider)
    custom = generator.generate_customization(resume, job_req, match_result)
    print("✨ Generated tailored application materials.")

    tracker = ApplicationTracker(db_path=args.db)
    record = tracker.add_application(
        company=job_req.company,
        role=job_req.title,
        job_url=args.url or "",
        match_score=match_result.overall_score,
        status=ApplicationStatus.APPLIED,
        notes=f"Auto-applied via pipeline. Match: {match_result.overall_score}%"
    )
    print(f"💾 Stored application record #{record.id} in tracking database.")

    if args.url:
        print(f"🤖 Launching auto-apply engine (dry-run: {args.dry_run})...")
        engine = AutoApplyEngine(headless=args.headless)
        apply_result = asyncio.run(engine.apply(
            job_url=args.url,
            resume=resume,
            customization=custom,
            resume_pdf_path=args.resume if args.resume.endswith(".pdf") else None,
            dry_run=args.dry_run
        ))
        print("Apply Result:", json.dumps(apply_result, indent=2))


def main() -> None:
    """Command-line argument router."""
    parser = argparse.ArgumentParser(description="Autonomous AI Job Application Agent CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: parse
    p_parse = subparsers.add_parser("parse", help="Parse resume file")
    p_parse.add_argument("--resume", required=True, help="Path to resume (.pdf, .txt, .md)")

    # Subcommand: analyze
    p_analyze = subparsers.add_parser("analyze", help="Analyze job description")
    p_analyze.add_argument("--job", required=True, help="Job description text or file path")
    p_analyze.add_argument("--title", default="Software Engineer", help="Job Title")
    p_analyze.add_argument("--company", default="Company", help="Company Name")

    # Subcommand: match
    p_match = subparsers.add_parser("match", help="Compute ATS match score")
    p_match.add_argument("--resume", required=True, help="Path to resume file")
    p_match.add_argument("--job", required=True, help="Job description text or file path")
    p_match.add_argument("--title", default="Software Engineer", help="Job Title")
    p_match.add_argument("--company", default="Company", help="Company Name")

    # Subcommand: tailor
    p_tailor = subparsers.add_parser("tailor", help="Generate tailored resume and cover letter")
    p_tailor.add_argument("--resume", required=True, help="Path to resume file")
    p_tailor.add_argument("--job", required=True, help="Job description text or file path")
    p_tailor.add_argument("--title", default="Software Engineer", help="Job Title")
    p_tailor.add_argument("--company", default="Company", help="Company Name")
    p_tailor.add_argument("--provider", default="mock", choices=["mock", "openai", "gemini"])

    # Subcommand: track
    p_track = subparsers.add_parser("track", help="Manage application database records")
    p_track.add_argument("--db", default="applications.db", help="SQLite database path")
    p_track.add_argument("--stats", action="store_true", help="Display application metrics")
    p_track.add_argument("--filter-status", help="Filter by status (Applied, Interview, Rejected, etc.)")
    p_track.add_argument("--search", help="Search keyword")
    p_track.add_argument("--update-id", type=int, help="Application ID to update")
    p_track.add_argument("--status", help="New status value")
    p_track.add_argument("--note", help="Note for update")

    # Subcommand: batch
    p_batch = subparsers.add_parser("batch", help="Run end-to-end autonomous pipeline")
    p_batch.add_argument("--resume", required=True, help="Path to resume file")
    p_batch.add_argument("--job", required=True, help="Job description text or file path")
    p_batch.add_argument("--title", default="Senior Python Engineer", help="Job Title")
    p_batch.add_argument("--company", default="Acme Corp", help="Company Name")
    p_batch.add_argument("--url", default="", help="Application URL")
    p_batch.add_argument("--min-score", type=float, default=60.0, help="Minimum ATS score to apply")
    p_batch.add_argument("--db", default="applications.db", help="SQLite database path")
    p_batch.add_argument("--provider", default="mock", choices=["mock", "openai", "gemini"])
    p_batch.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode")
    p_batch.add_argument("--dry-run", action="store_true", default=True, help="Verify fields without submitting")

    args = parser.parse_args()

    handlers = {
        "parse": handle_parse,
        "analyze": handle_analyze,
        "match": handle_match,
        "tailor": handle_tailor,
        "track": handle_track,
        "batch": handle_batch
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()
