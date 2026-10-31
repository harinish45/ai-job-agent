"""
LLM Generator Module for Tailored Resumes and Cover Letters.
Compatible with OpenAI and Google Gemini APIs, with high-quality mock fallback.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from src.models import (
    ATSMatchResult,
    CustomizationResult,
    JobRequirement,
    ResumeData,
)

logger = logging.getLogger(__name__)


class LLMGeneratorError(Exception):
    """Raised when LLM generation fails unexpectedly."""
    pass


class LLMGenerator:
    """Generates tailored resume bullets, summaries, and cover letters using LLMs."""

    def __init__(
        self,
        provider: str = "mock",
        api_key: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "mock")).lower()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
        self.model_name = model_name or self._default_model_for_provider()

    def generate_customization(
        self,
        resume: ResumeData,
        job: JobRequirement,
        match: ATSMatchResult
    ) -> CustomizationResult:
        """Generate tailored summary, bullets, cover letter, and screening answers."""
        if not resume or not job:
            raise LLMGeneratorError("Resume and JobRequirement cannot be None.")

        # Check if live LLM is requested and configured
        if self.provider == "openai" and self.api_key:
            try:
                return self._generate_with_openai(resume, job, match)
            except Exception as exc:
                logger.warning("OpenAI generation failed (%s), falling back to mock generator.", exc)
        elif self.provider == "gemini" and self.api_key:
            try:
                return self._generate_with_gemini(resume, job, match)
            except Exception as exc:
                logger.warning("Gemini generation failed (%s), falling back to mock generator.", exc)

        logger.info("Using mock/template generator for application customization.")
        return self._generate_mock(resume, job, match)

    def _generate_mock(
        self,
        resume: ResumeData,
        job: JobRequirement,
        match: ATSMatchResult
    ) -> CustomizationResult:
        """High-fidelity template generator for offline, test, or mock environments."""
        candidate_name = resume.contact.name or "Candidate"
        company = job.company or "the engineering team"
        role = job.title or "Software Engineer"
        top_skills = ", ".join(match.matched_skills[:4]) if match.matched_skills else "software development"
        missing_skills = match.missing_skills[:3]

        # Tailored summary
        summary = (
            f"Results-driven professional with {resume.years_of_experience:.0f}+ years of experience, "
            f"specializing in {top_skills}. Proven track record designing scalable solutions and "
            f"delivering robust business impact at {company} as {role}."
        )

        # Tailored bullets
        tailored_bullets: Dict[str, List[str]] = {}
        for exp in resume.experience[:3]:
            bullets: List[str] = []
            for b in (exp.achievements or [exp.description]):
                bullet_text = b if b else "Engineered high-performance backend microservices"
                bullets.append(f"Architected scalable systems leveraging {top_skills}, optimizing execution efficiency by 35%: {bullet_text}")
            tailored_bullets[exp.company] = bullets[:3]

        # Cover letter
        cover_letter = self._build_mock_cover_letter(
            candidate_name, role, company, top_skills, resume.years_of_experience, resume.contact.email
        )

        why_company = f"I am excited by {company}'s commitment to innovation and technical excellence."
        why_role = f"This {role} position matches my core strengths in {top_skills} and my passion for building resilient systems."

        return CustomizationResult(
            tailored_summary=summary,
            tailored_bullets=tailored_bullets,
            cover_letter=cover_letter,
            ats_keywords_to_include=match.missing_skills[:5] + match.ats_keywords_missing[:5],
            why_company=why_company,
            why_role=why_role
        )

    def _build_mock_cover_letter(
        self,
        name: str,
        role: str,
        company: str,
        skills: str,
        years: float,
        email: str
    ) -> str:
        """Assemble structured professional cover letter."""
        return (
            f"Dear Hiring Team at {company},\n\n"
            f"I am writing to express my strong enthusiasm for the {role} position. "
            f"With over {years:.0f} years of hands-on experience specializing in {skills}, "
            f"I have consistently built robust, scalable solutions and led collaborative teams to success.\n\n"
            f"At previous organizations, I focused on reducing latency, improving code coverage, and "
            f"shipping critical features on schedule. The mission of {company} strongly aligns with my career goals, "
            f"and I am eager to contribute immediately to your product roadmap.\n\n"
            f"Thank you for your time and consideration. I welcome the opportunity to discuss how my "
            f"background and technical skills can benefit {company}.\n\n"
            f"Sincerely,\n{name}\n{email}"
        )

    def _generate_with_openai(
        self,
        resume: ResumeData,
        job: JobRequirement,
        match: ATSMatchResult
    ) -> CustomizationResult:
        """Call OpenAI API with structured prompting."""
        import openai
        client = openai.OpenAI(api_key=self.api_key)
        prompt = self._build_prompt(resume, job, match)

        response = client.chat.completions.create(
            model=self.model_name or "gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an expert career coach and ATS optimization specialist. Output strictly valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        data = json.loads(response.choices[0].message.content or "{}")
        return self._parse_json_result(data, resume, job, match)

    def _generate_with_gemini(
        self,
        resume: ResumeData,
        job: JobRequirement,
        match: ATSMatchResult
    ) -> CustomizationResult:
        """Call Google Gemini API via google-genai or httpx."""
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            prompt = self._build_prompt(resume, job, match)
            response = client.models.generate_content(
                model=self.model_name or "gemini-2.0-flash",
                contents=prompt
            )
            raw_text = response.text or "{}"
            # Clean possible markdown fence
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            data = json.loads(raw_text)
            return self._parse_json_result(data, resume, job, match)
        except Exception as exc:
            logger.error("Gemini invocation failed: %s", exc)
            raise LLMGeneratorError(f"Gemini API failure: {exc}") from exc

    def _build_prompt(self, resume: ResumeData, job: JobRequirement, match: ATSMatchResult) -> str:
        """Construct structured prompt for LLM tailoring."""
        return (
            f"Optimize candidate application materials for ATS and recruiter review.\n\n"
            f"CANDIDATE:\nName: {resume.contact.name}\nSkills: {', '.join(resume.skills)}\n"
            f"Years Experience: {resume.years_of_experience}\n\n"
            f"JOB:\nRole: {job.title}\nCompany: {job.company}\nRequired: {', '.join(job.required_skills)}\n\n"
            f"MATCH ANALYSIS:\nMatched Skills: {', '.join(match.matched_skills)}\n"
            f"Missing Skills: {', '.join(match.missing_skills)}\n\n"
            f"Return JSON with keys: tailored_summary, tailored_bullets (mapping company to array of bullets), "
            f"cover_letter (300 words), why_company, why_role."
        )

    def _parse_json_result(
        self,
        data: Dict[str, Any],
        resume: ResumeData,
        job: JobRequirement,
        match: ATSMatchResult
    ) -> CustomizationResult:
        """Convert LLM response dict into CustomizationResult."""
        return CustomizationResult(
            tailored_summary=data.get("tailored_summary", ""),
            tailored_bullets=data.get("tailored_bullets", {}),
            cover_letter=data.get("cover_letter", ""),
            ats_keywords_to_include=match.missing_skills[:5],
            why_company=data.get("why_company", ""),
            why_role=data.get("why_role", "")
        )

    def _default_model_for_provider(self) -> str:
        """Default model name per provider."""
        if self.provider == "openai":
            return "gpt-4-turbo-preview"
        elif self.provider == "gemini":
            return "gemini-2.0-flash"
        return "mock-deterministic"
