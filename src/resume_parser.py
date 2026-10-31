"""
Resume parser module.
Extracts contact information, education, skills, and work experience from text or PDF files.
"""

import io
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

from src.models import (
    ContactInfo,
    EducationEntry,
    ExperienceEntry,
    ResumeData,
    SeniorityLevel,
)

logger = logging.getLogger(__name__)


class ResumeParserError(Exception):
    """Raised when resume parsing encounters an unrecoverable issue."""
    pass


class ResumeParser:
    """Parser for raw text and PDF resume documents."""

    SKILLS_TAXONOMY: Dict[str, List[str]] = {
        "programming": [
            "python", "javascript", "typescript", "java", "c++", "c#", "go",
            "rust", "scala", "ruby", "php", "swift", "kotlin", "sql", "bash"
        ],
        "frameworks": [
            "fastapi", "flask", "django", "react", "next.js", "vue", "angular",
            "node.js", "express", "spring", "spring boot", "rails", "asp.net"
        ],
        "ai_ml": [
            "machine learning", "deep learning", "nlp", "computer vision", "llm",
            "pytorch", "tensorflow", "keras", "scikit-learn", "huggingface",
            "langchain", "openai", "transformers", "xgboost", "rag"
        ],
        "cloud_devops": [
            "aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ci/cd",
            "github actions", "gitlab", "ansible", "linux", "helm"
        ],
        "data_engineering": [
            "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
            "spark", "hadoop", "kafka", "airflow", "snowflake", "pandas", "numpy"
        ],
        "soft_skills": [
            "leadership", "mentoring", "cross-functional", "communication",
            "problem solving", "agile", "scrum", "project management"
        ]
    }

    DEGREE_PATTERNS: List[Tuple[str, str]] = [
        (r"\b(ph\.?d\.?|doctor\s+of\s+philosophy)\b", "Ph.D."),
        (r"\b(master\s+of\s+science|m\.?s\.?|m\.?sc\.?|master's)\b", "Master of Science"),
        (r"\b(master\s+of\s+business\s+administration|mba)\b", "MBA"),
        (r"\b(bachelor\s+of\s+science|b\.?s\.?|b\.?sc\.?|bachelor's)\b", "Bachelor of Science"),
        (r"\b(bachelor\s+of\s+engineering|b\.?e\.?|b\.?tech\.?)\b", "B.Tech/B.E."),
        (r"\b(bachelor\s+of\s+arts|b\.?a\.?)\b", "Bachelor of Arts"),
    ]

    def parse(self, text: str) -> ResumeData:
        """Parse raw resume text into structured ResumeData."""
        if not text or not text.strip():
            raise ResumeParserError("Resume text cannot be empty.")

        cleaned_text = self._normalize_text(text)
        contact = self.extract_contact(cleaned_text)
        skills = self.extract_skills(cleaned_text)
        education = self.extract_education(cleaned_text)
        experience = self.extract_experience(cleaned_text)
        years = self._estimate_years_experience(cleaned_text, experience)
        seniority = self._determine_seniority(years)
        summary = self._extract_summary(cleaned_text)

        logger.info("Successfully parsed resume for '%s'", contact.name or "Unknown")
        return ResumeData(
            contact=contact,
            summary=summary,
            skills=skills,
            experience=experience,
            education=education,
            certifications=self._extract_certifications(cleaned_text),
            years_of_experience=years,
            detected_seniority=seniority,
            raw_text=text,
        )

    def parse_file(self, file_path: str) -> ResumeData:
        """Parse resume from a file path (.txt, .md, or .pdf)."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Resume file not found at: {file_path}")

        suffix = path.suffix.lower()
        if suffix == ".pdf":
            text = self.extract_text_from_pdf(file_path)
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")

        return self.parse(text)

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract plain text from PDF using pypdf."""
        if not HAS_PYPDF:
            raise ResumeParserError("pypdf is required for PDF parsing. Please install pypdf.")

        try:
            reader = PdfReader(pdf_path)
            extracted_pages: List[str] = []
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                if page_text:
                    extracted_pages.append(page_text)
            full_text = "\n".join(extracted_pages)
            if not full_text.strip():
                raise ResumeParserError(f"PDF at {pdf_path} yielded no extractable text.")
            return full_text
        except Exception as exc:
            logger.error("Failed to parse PDF %s: %s", pdf_path, exc)
            raise ResumeParserError(f"Error reading PDF file: {exc}") from exc

    def extract_contact(self, text: str) -> ContactInfo:
        """Extract email, phone, links, and candidate name."""
        email = self._extract_regex(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text
        )
        phone = self._extract_regex(
            r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text
        )
        linkedin = self._extract_regex(
            r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|profile)/[A-Za-z0-9_-]+", text
        )
        github = self._extract_regex(
            r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_-]+", text
        )
        portfolio = self._extract_regex(
            r"(?:https?://)?(?:www\.)?[A-Za-z0-9_-]+\.(?:dev|io|me|portfolio|com)", text
        )
        name = self._extract_candidate_name(text)

        return ContactInfo(
            name=name,
            email=email,
            phone=phone,
            linkedin=linkedin,
            github=github,
            portfolio=portfolio,
        )

    def extract_skills(self, text: str) -> List[str]:
        """Match and deduplicate skills based on taxonomy and keyword mentions."""
        text_lower = text.lower()
        found_skills: Set[str] = set()

        for category_skills in self.SKILLS_TAXONOMY.values():
            for skill in category_skills:
                # Word boundary match to avoid false substrings
                pattern = r"\b" + re.escape(skill) + r"\b"
                if re.search(pattern, text_lower):
                    found_skills.add(skill)

        return sorted(list(found_skills))

    def extract_education(self, text: str) -> List[EducationEntry]:
        """Extract academic degree credentials and institutions."""
        entries: List[EducationEntry] = []
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        for i, line in enumerate(lines):
            line_lower = line.lower()
            for pattern, degree_name in self.DEGREE_PATTERNS:
                if re.search(pattern, line_lower):
                    institution = self._find_institution(lines, i)
                    grad_year = None
                    for offset in range(0, min(4, len(lines) - i)):
                        found_year = self._find_year(lines[i + offset])
                        if found_year:
                            grad_year = found_year
                            break
                    entries.append(EducationEntry(
                        institution=institution,
                        degree=degree_name,
                        graduation_year=grad_year
                    ))
                    break

        return entries

    def extract_experience(self, text: str) -> List[ExperienceEntry]:
        """Extract job titles, companies, dates, and achievements."""
        entries: List[ExperienceEntry] = []
        pattern = r"(?P<role>[A-Z][A-Za-z\t ]{2,40})\s+(?:at|@)\s+(?P<company>[A-Z][A-Za-z0-9\t ,\.\-]{2,40})"
        matches = list(re.finditer(pattern, text))

        for idx, match in enumerate(matches):
            role = match.group("role").strip()
            company = match.group("company").strip()
            # Capture following text as bullet points until next match
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else start + 600
            snippet = text[start:end]
            bullets = [
                b.strip("-*• ") for b in snippet.split("\n")
                if b.strip().startswith(("-", "*", "•"))
            ]
            entries.append(ExperienceEntry(
                company=company,
                role=role,
                achievements=bullets[:5],
                description=snippet.strip()[:200]
            ))

        return entries

    def _extract_candidate_name(self, text: str) -> str:
        """Extract candidate name from header lines."""
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines[:5]:
            # Look for line with 2-4 capitalized words without special chars
            if re.match(r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}$", line):
                return line
        return lines[0] if lines else "Candidate"

    def _extract_summary(self, text: str) -> str:
        """Extract professional summary block if present."""
        match = re.search(
            r"(?:summary|objective|profile|about me)[\s:]*\n+([^\n]+(?:\n[^\n]+){1,4})",
            text,
            re.IGNORECASE,
        )
        return match.group(1).strip() if match else ""

    def _extract_certifications(self, text: str) -> List[str]:
        """Extract recognized professional certifications."""
        cert_keywords = [
            "aws certified", "azure certified", "gcp certified",
            "pmp", "cissp", "cka", "ckad", "scrum master"
        ]
        text_lower = text.lower()
        return [cert for cert in cert_keywords if cert in text_lower]

    def _find_institution(self, lines: List[str], current_index: int) -> str:
        """Find university or college name near degree line."""
        keywords = ["university", "college", "institute", "school", "academy"]
        check_range = range(max(0, current_index - 1), min(len(lines), current_index + 2))
        for idx in check_range:
            line = lines[idx]
            if any(kw in line.lower() for kw in keywords):
                return line.strip()
        return "Accredited University"

    def _find_year(self, text: str) -> Optional[int]:
        """Find 4-digit graduation year between 1980 and 2030."""
        match = re.search(r"\b(19[89]\d|20[0-3]\d)\b", text)
        return int(match.group(1)) if match else None

    def _estimate_years_experience(self, text: str, experiences: List[ExperienceEntry]) -> float:
        """Estimate total professional experience in years."""
        explicit_match = re.search(r"(\d+(?:\.\d+)?)\+?\s*years?(?:\s+of)?\s+experience", text, re.IGNORECASE)
        if explicit_match:
            return float(explicit_match.group(1))
        if experiences:
            return float(max(len(experiences) * 2.0, 1.0))
        return 2.0

    def _determine_seniority(self, years: float) -> SeniorityLevel:
        """Map total experience years to SeniorityLevel."""
        if years < 1.0:
            return SeniorityLevel.INTERN
        elif years < 3.0:
            return SeniorityLevel.ENTRY
        elif years < 6.0:
            return SeniorityLevel.MID
        elif years < 10.0:
            return SeniorityLevel.SENIOR
        elif years < 15.0:
            return SeniorityLevel.LEAD
        return SeniorityLevel.EXECUTIVE

    def _extract_regex(self, pattern: str, text: str) -> str:
        """Extract first regex match string or return empty string."""
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(0).strip() if match else ""

    def _normalize_text(self, text: str) -> str:
        """Normalize line endings and multiple spaces."""
        return re.sub(r"[ \t]+", " ", text.replace("\r\n", "\n"))
