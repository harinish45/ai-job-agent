"""
Resume Intelligence Service
Parses resumes using OCR + NLP, extracts structured data,
detects strengths/gaps, and suggests improvements.
"""
import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import openai
from app.config import get_settings

settings = get_settings()
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

class ResumeParser:
    """Production-grade resume parser with AI enhancement."""

    AI_ROLE_KEYWORDS = [
        "prompt engineer", "ai operations", "automation specialist",
        "ai product analyst", "ai trainer", "ai safety reviewer",
        "data labeling lead", "workflow automation engineer",
        "cybersecurity ai analyst", "ml engineer", "machine learning",
        "deep learning", "nlp", "computer vision", "llm", "genai",
        "ai researcher", "ai strategist", "robotics", "autonomous systems"
    ]

    def __init__(self):
        self.skills_taxonomy = self._load_skills_taxonomy()

    def _load_skills_taxonomy(self) -> Dict:
        """Load comprehensive skills taxonomy."""
        return {
            "programming": ["python", "javascript", "typescript", "java", "c++", "go", "rust", "scala", "r", "julia"],
            "ai_ml": ["tensorflow", "pytorch", "scikit-learn", "keras", "huggingface", "langchain", "openai", "llama", "xgboost", "lightgbm"],
            "data": ["sql", "postgresql", "mongodb", "spark", "hadoop", "kafka", "airflow", "dbt", "pandas", "numpy"],
            "cloud": ["aws", "gcp", "azure", "docker", "kubernetes", "terraform", "serverless"],
            "web": ["react", "next.js", "vue", "angular", "fastapi", "django", "flask", "node.js", "graphql"],
            "soft": ["leadership", "communication", "problem solving", "teamwork", "agile", "scrum"]
        }

    async def parse_resume(self, resume_text: str, file_type: str = "pdf") -> Dict[str, Any]:
        """
        Main entry point: Parse raw resume text into structured data.
        """
        # Phase 1: Basic extraction
        basic_data = self._extract_basic_info(resume_text)

        # Phase 2: AI-powered deep parsing
        ai_data = await self._ai_parse_resume(resume_text)

        # Phase 3: Merge and enrich
        structured = self._merge_and_enrich(basic_data, ai_data, resume_text)

        # Phase 4: Analysis
        structured["analysis"] = self._analyze_profile(structured)

        # Phase 5: Suggestions
        structured["suggestions"] = self._generate_suggestions(structured)

        return structured

    def _extract_basic_info(self, text: str) -> Dict:
        """Extract basic info using regex patterns."""
        # Email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)

        # Phone
        phone_pattern = r'(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
        phones = re.findall(phone_pattern, text)

        # LinkedIn
        linkedin_pattern = r'(?:linkedin\.com/in/|linkedin\.com/profile/)[A-Za-z0-9_-]+'
        linkedin = re.findall(linkedin_pattern, text)

        # GitHub
        github_pattern = r'(?:github\.com/)[A-Za-z0-9_-]+'
        github = re.findall(github_pattern, text)

        # Education keywords
        education_keywords = ["bachelor", "master", "phd", "doctorate", "bs", "ms", "mba", "b.s.", "m.s.", "b.e.", "m.e."]
        has_education = any(kw in text.lower() for kw in education_keywords)

        return {
            "contact": {
                "email": emails[0] if emails else None,
                "phone": phones[0] if phones else None,
                "linkedin": linkedin[0] if linkedin else None,
                "github": github[0] if github else None,
            },
            "has_education_section": has_education,
            "raw_text_length": len(text)
        }

    async def _ai_parse_resume(self, text: str) -> Dict:
        """Use OpenAI to deeply parse resume structure."""
        prompt = f"""
        You are an expert resume parser. Extract structured data from this resume.

        Resume Text:
        {text[:8000]}  # Truncate to fit token limits

        Return ONLY valid JSON with this exact structure:
        {{
            "name": "Full Name",
            "title": "Current/Most Recent Job Title",
            "summary": "Professional summary",
            "experience": [
                {{
                    "company": "Company Name",
                    "title": "Job Title",
                    "location": "City, State/Remote",
                    "start_date": "YYYY-MM",
                    "end_date": "YYYY-MM or Present",
                    "description": "Job description",
                    "achievements": ["achievement 1", "achievement 2"],
                    "skills_used": ["skill1", "skill2"]
                }}
            ],
            "education": [
                {{
                    "institution": "University Name",
                    "degree": "Degree Type",
                    "field": "Field of Study",
                    "graduation_date": "YYYY-MM",
                    "gpa": "X.X"
                }}
            ],
            "projects": [
                {{
                    "name": "Project Name",
                    "description": "What it does",
                    "technologies": ["tech1", "tech2"],
                    "url": "github or demo link"
                }}
            ],
            "skills": ["skill1", "skill2"],
            "certifications": ["cert1", "cert2"],
            "languages": ["language1", "language2"],
            "years_of_experience": 5.5,
            "industries": ["industry1", "industry2"],
            "target_roles": ["role1", "role2"]
        }}

        Rules:
        - Infer target roles from experience and skills
        - Calculate years_of_experience from dates
        - Extract ALL skills mentioned
        - Be precise with dates
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a precise resume parser. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )

            content = response.choices[0].message.content
            # Clean up markdown code blocks if present
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)

            return json.loads(content)
        except Exception as e:
            return {"error": str(e), "partial": True}

    def _merge_and_enrich(self, basic: Dict, ai: Dict, raw_text: str) -> Dict:
        """Merge basic and AI extraction, add computed fields."""
        merged = {
            "name": ai.get("name", "Unknown"),
            "title": ai.get("title", ""),
            "summary": ai.get("summary", ""),
            "contact": {
                **basic.get("contact", {}),
                "email": basic.get("contact", {}).get("email") or ai.get("email", ""),
            },
            "experience": ai.get("experience", []),
            "education": ai.get("education", []),
            "projects": ai.get("projects", []),
            "skills": list(set(
                (ai.get("skills", []) or []) +
                self._extract_skills_from_text(raw_text)
            )),
            "certifications": ai.get("certifications", []),
            "languages": ai.get("languages", []),
            "years_of_experience": ai.get("years_of_experience", 0),
            "industries": ai.get("industries", []),
            "target_roles": ai.get("target_roles", []),
            "raw_text": raw_text,
        }

        # Enrich with AI role detection
        merged["is_ai_professional"] = self._detect_ai_professional(merged)
        merged["ai_role_categories"] = self._categorize_ai_role(merged)

        return merged

    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills using taxonomy matching."""
        text_lower = text.lower()
        found_skills = []

        for category, skills in self.skills_taxonomy.items():
            for skill in skills:
                if skill.lower() in text_lower:
                    found_skills.append(skill)

        return found_skills

    def _detect_ai_professional(self, profile: Dict) -> bool:
        """Detect if candidate is in AI field."""
        text = profile.get("raw_text", "").lower()
        skills = [s.lower() for s in profile.get("skills", [])]

        ai_indicators = self.AI_ROLE_KEYWORDS + [
            "machine learning", "deep learning", "neural network",
            "transformer", "gpt", "llm", "fine-tuning", "model training",
            "inference", "embedding", "vector database", "rag"
        ]

        return any(ind in text or ind in skills for ind in ai_indicators)

    def _categorize_ai_role(self, profile: Dict) -> List[str]:
        """Categorize into specific AI role types."""
        text = profile.get("raw_text", "").lower()
        skills = [s.lower() for s in profile.get("skills", [])]
        title = profile.get("title", "").lower()

        categories = []

        role_mappings = {
            "prompt_engineer": ["prompt", "prompting", "llm tuning", "instruction tuning"],
            "ml_engineer": ["ml pipeline", "model deployment", "feature engineering", "mlops"],
            "ai_researcher": ["research", "paper", "publication", "novel architecture"],
            "ai_product": ["product", "roadmap", "stakeholder", "ai strategy"],
            "data_scientist": ["statistics", "experiment", "a/b test", "hypothesis"],
            "ai_ops": ["infrastructure", "scaling", "gpu", "distributed training"],
            "ai_safety": ["safety", "alignment", "rlhf", "red teaming", "evaluation"],
            "automation": ["automation", "rpa", "workflow", "orchestration"],
        }

        for category, indicators in role_mappings.items():
            if any(ind in text or ind in title or ind in skills for ind in indicators):
                categories.append(category)

        return categories

    def _analyze_profile(self, profile: Dict) -> Dict:
        """Analyze strengths, gaps, and transferable skills."""
        skills = set(profile.get("skills", []))
        experience = profile.get("experience", [])
        years = profile.get("years_of_experience", 0)

        # Strengths
        strengths = []
        if years >= 5:
            strengths.append("Strong experience depth")
        if len(skills) >= 10:
            strengths.append("Diverse technical skillset")
        if any("lead" in exp.get("title", "").lower() or "manager" in exp.get("title", "").lower() for exp in experience):
            strengths.append("Leadership experience")
        if profile.get("projects"):
            strengths.append("Portfolio of projects")
        if profile.get("is_ai_professional"):
            strengths.append("AI/ML specialization")

        # Gaps
        gaps = []
        if years < 2:
            gaps.append("Limited professional experience")
        if not any("cloud" in s.lower() for s in skills):
            gaps.append("No cloud platform experience listed")
        if not profile.get("education"):
            gaps.append("Education section missing or unclear")
        if not profile.get("certifications"):
            gaps.append("No certifications listed")

        # Transferable skills
        transferable = []
        if any("python" in s.lower() for s in skills):
            transferable.extend(["Data Analysis", "Automation", "Scripting"])
        if any("sql" in s.lower() for s in skills):
            transferable.extend(["Data Management", "Business Intelligence"])
        if any("react" in s.lower() or "frontend" in s.lower() for s in skills):
            transferable.extend(["UI/UX Understanding", "User-Centric Development"])

        return {
            "strengths": strengths,
            "gaps": gaps,
            "transferable_skills": list(set(transferable)),
            "experience_level": self._determine_level(years, skills),
            "skill_depth": len(skills),
            "recommendation_summary": f"Strong candidate with {len(strengths)} key strengths and {len(gaps)} areas for development."
        }

    def _determine_level(self, years: float, skills: set) -> str:
        if years < 1:
            return "intern"
        elif years < 3:
            return "entry"
        elif years < 6:
            return "mid"
        elif years < 10:
            return "senior"
        else:
            return "staff"

    def _generate_suggestions(self, profile: Dict) -> List[Dict]:
        """Generate resume improvement suggestions."""
        suggestions = []

        if len(profile.get("raw_text", "")) < 1000:
            suggestions.append({
                "category": "content",
                "priority": "high",
                "suggestion": "Resume appears too short. Add more detail about achievements with metrics."
            })

        if not profile.get("projects"):
            suggestions.append({
                "category": "projects",
                "priority": "medium",
                "suggestion": "Add a projects section to showcase practical application of skills."
            })

        for exp in profile.get("experience", []):
            desc = exp.get("description", "")
            if not re.search(r'\d+%|\d+x|\$\d+|increased|decreased|improved|reduced', desc.lower()):
                suggestions.append({
                    "category": "metrics",
                    "priority": "high",
                    "suggestion": f"Add quantifiable achievements to {exp.get('title', 'role')} at {exp.get('company', 'company')}."
                })

        if not any(s.lower() in [sk.lower() for sk in profile.get("skills", [])] for s in ["communication", "leadership", "teamwork"]):
            suggestions.append({
                "category": "soft_skills",
                "priority": "low",
                "suggestion": "Consider adding soft skills or demonstrating them through experience descriptions."
            })

        return suggestions


# Celery task wrapper
from app.core.celery_app import celery_app

@celery_app.task(bind=True, max_retries=3)
def parse_resume_task(self, resume_text: str, file_type: str = "pdf"):
    """Celery task for async resume parsing."""
    import asyncio
    parser = ResumeParser()
    try:
        return asyncio.run(parser.parse_resume(resume_text, file_type))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
