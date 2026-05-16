"""
Intelligent Job Matching Engine
Calculates multi-dimensional match scores between candidate profile and job listings.
Uses embeddings + rule-based scoring for production reliability.
"""
import json
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import openai
from app.config import get_settings

settings = get_settings()
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

class JobMatcher:
    """
    Production-grade job matching with explainable scores.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            stop_words='english',
            lowercase=True
        )
        self.weights = {
            "skills": 0.30,
            "experience": 0.20,
            "role": 0.20,
            "location": 0.10,
            "salary": 0.10,
            "culture": 0.10,
        }

    async def calculate_match(
        self,
        profile: Dict[str, Any],
        job: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive match score between profile and job.
        Returns detailed scoring breakdown.
        """
        # Individual dimension scores
        skills_score, matching_skills, missing_skills = self._match_skills(
            profile.get("skills", []),
            job.get("skills_required", []),
            job.get("description", "")
        )

        experience_score = self._match_experience(
            profile.get("years_of_experience", 0),
            profile.get("experience", []),
            job.get("experience_level"),
            job.get("description", "")
        )

        role_score = self._match_role(
            profile.get("target_roles", []),
            profile.get("title", ""),
            job.get("title", ""),
            job.get("description", "")
        )

        location_score = self._match_location(
            profile.get("location", ""),
            profile.get("preferred_locations", []),
            profile.get("work_mode_preference", "remote"),
            job.get("location", ""),
            job.get("work_mode", "remote")
        )

        salary_score = self._match_salary(
            profile.get("min_salary"),
            profile.get("max_salary"),
            job.get("salary_min"),
            job.get("salary_max")
        )

        culture_score = await self._match_culture(
            profile,
            job
        )

        # Weighted overall score
        overall = (
            skills_score * self.weights["skills"] +
            experience_score * self.weights["experience"] +
            role_score * self.weights["role"] +
            location_score * self.weights["location"] +
            salary_score * self.weights["salary"] +
            culture_score * self.weights["culture"]
        )

        # Generate recommendation
        recommendation = self._generate_recommendation(
            overall, skills_score, experience_score, missing_skills
        )

        # Identify transferable skills applicable
        transferable_applicable = self._find_transferable_applications(
            profile.get("transferable_skills", []),
            missing_skills,
            job.get("description", "")
        )

        return {
            "overall_score": round(overall, 3),
            "skills_match": round(skills_score, 3),
            "experience_match": round(experience_score, 3),
            "role_match": round(role_score, 3),
            "location_match": round(location_score, 3),
            "salary_match": round(salary_score, 3),
            "culture_match": round(culture_score, 3),
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "transferable_skills_applicable": transferable_applicable,
            "gap_analysis": self._generate_gap_analysis(missing_skills, transferable_applicable),
            "recommendation": recommendation,
            "is_strong_match": overall >= settings.MATCH_SCORE_THRESHOLD,
            "calculated_at": datetime.utcnow().isoformat()
        }

    def _match_skills(
        self,
        candidate_skills: List[str],
        job_skills: List[str],
        job_description: str
    ) -> Tuple[float, List[str], List[str]]:
        """
        Match skills with semantic understanding.
        Returns (score, matching, missing)
        """
        if not candidate_skills:
            return 0.0, [], job_skills or []

        candidate_skills_lower = [s.lower().strip() for s in candidate_skills]
        job_skills_lower = [s.lower().strip() for s in (job_skills or [])]

        # Direct matches
        matching = []
        missing = []

        for job_skill in job_skills_lower:
            # Exact or substring match
            if any(job_skill in cs or cs in job_skill for cs in candidate_skills_lower):
                matching.append(job_skill)
            else:
                # Check description for context
                missing.append(job_skill)

        # Also extract skills from description that candidate has
        desc_words = set(job_description.lower().split())
        for cs in candidate_skills_lower:
            if cs in desc_words and cs not in matching:
                matching.append(cs)

        # Calculate score
        total_required = len(job_skills_lower) if job_skills_lower else 1
        score = len(matching) / total_required if total_required > 0 else 0.5

        # Boost for high skill overlap
        if score >= 0.8:
            score = min(1.0, score + 0.05)

        return min(1.0, score), matching, missing

    def _match_experience(
        self,
        years: float,
        experiences: List[Dict],
        job_level: Optional[str],
        job_description: str
    ) -> float:
        """Match experience level requirements."""
        level_requirements = {
            "intern": (0, 1),
            "entry": (0, 2),
            "mid": (2, 5),
            "senior": (5, 8),
            "staff": (8, 12),
            "principal": (10, 20),
            "executive": (10, 30)
        }

        if not job_level:
            # Infer from description
            desc_lower = job_description.lower()
            if "senior" in desc_lower or "sr." in desc_lower:
                job_level = "senior"
            elif "staff" in desc_lower or "principal" in desc_lower:
                job_level = "staff"
            elif "lead" in desc_lower or "manager" in desc_lower:
                job_level = "senior"
            elif "junior" in desc_lower or "jr." in desc_lower or "entry" in desc_lower:
                job_level = "entry"
            else:
                job_level = "mid"

        req_min, req_max = level_requirements.get(job_level, (0, 10))

        if years >= req_min:
            if years <= req_max * 1.5:  # Allow some over-qualification
                return 1.0
            else:
                return 0.85  # Slightly penalize over-qualification
        else:
            gap = req_min - years
            if gap <= 1:
                return 0.8
            elif gap <= 2:
                return 0.6
            else:
                return max(0.2, 0.5 - (gap * 0.1))

    def _match_role(
        self,
        target_roles: List[str],
        current_title: str,
        job_title: str,
        job_description: str
    ) -> float:
        """Match target role preferences with job title."""
        job_title_lower = job_title.lower()
        current_title_lower = current_title.lower()

        # Direct title match
        if any(tr.lower() in job_title_lower for tr in target_roles):
            return 1.0

        # Current title match
        if current_title_lower and any(ct in job_title_lower for ct in current_title_lower.split()):
            return 0.9

        # Semantic similarity using TF-IDF
        texts = [
            " ".join(target_roles + [current_title]),
            job_title + " " + job_description[:500]
        ]

        try:
            tfidf_matrix = self.vectorizer.fit_transform(texts)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except:
            # Fallback: keyword overlap
            target_words = set(" ".join(target_roles).lower().split())
            job_words = set(job_title_lower.split() + job_description.lower().split()[:50])
            overlap = len(target_words & job_words)
            return min(1.0, overlap / max(len(target_words), 1))

    def _match_location(
        self,
        candidate_location: str,
        preferred_locations: List[str],
        work_mode_pref: str,
        job_location: str,
        job_work_mode: str
    ) -> float:
        """Match location and work mode preferences."""
        # Work mode is highest priority
        mode_scores = {
            ("remote", "remote"): 1.0,
            ("remote", "hybrid"): 0.7,
            ("remote", "onsite"): 0.1,
            ("hybrid", "hybrid"): 1.0,
            ("hybrid", "remote"): 0.9,
            ("hybrid", "onsite"): 0.4,
            ("onsite", "onsite"): 1.0,
            ("onsite", "hybrid"): 0.8,
            ("onsite", "remote"): 0.2,
        }

        mode_score = mode_scores.get(
            (work_mode_pref.lower(), (job_work_mode or "remote").lower()),
            0.5
        )

        # Location match
        location_score = 0.5
        job_loc_lower = (job_location or "").lower()

        if "remote" in job_loc_lower or job_work_mode == "remote":
            location_score = 1.0
        elif any(pref.lower() in job_loc_lower for pref in (preferred_locations or [])):
            location_score = 1.0
        elif candidate_location and candidate_location.lower() in job_loc_lower:
            location_score = 0.9

        return (mode_score * 0.6) + (location_score * 0.4)

    def _match_salary(
        self,
        candidate_min: Optional[int],
        candidate_max: Optional[int],
        job_min: Optional[int],
        job_max: Optional[int]
    ) -> float:
        """Match salary expectations."""
        if not candidate_min and not job_min:
            return 0.5  # Unknown on both sides

        if not job_min:
            return 0.7  # Job doesn't disclose

        if not candidate_min:
            return 0.7  # Candidate didn't specify

        # Normalize to annual
        candidate_target = candidate_min
        job_target = job_min

        if job_target >= candidate_target:
            if job_target <= (candidate_max or candidate_target * 1.5):
                return 1.0
            else:
                return 0.95  # Exceeds expectations
        else:
            gap = (candidate_target - job_target) / candidate_target
            return max(0.0, 1.0 - gap)

    async def _match_culture(
        self,
        profile: Dict,
        job: Dict
    ) -> float:
        """Use AI to assess culture/values fit."""
        try:
            prompt = f"""
            Rate the culture fit between this candidate and job on a scale of 0.0 to 1.0.

            Candidate Summary: {profile.get("summary", "")[:500]}
            Candidate Industries: {profile.get("industries", [])}

            Job Description: {job.get("description", "")[:1000]}
            Company: {job.get("company", "")}

            Consider: company size fit, industry alignment, growth trajectory, work style.
            Return ONLY a number between 0.0 and 1.0.
            """

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10
            )

            content = response.choices[0].message.content.strip()
            score = float(re.search(r'\d+\.?\d*', content).group())
            return min(1.0, max(0.0, score))
        except:
            return 0.5  # Neutral default

    def _find_transferable_applications(
        self,
        transferable_skills: List[str],
        missing_skills: List[str],
        job_description: str
    ) -> List[str]:
        """Find which transferable skills apply to missing requirements."""
        applicable = []
        desc_lower = job_description.lower()

        for ts in transferable_skills:
            if ts.lower() in desc_lower:
                applicable.append(ts)

        return applicable

    def _generate_gap_analysis(
        self,
        missing_skills: List[str],
        transferable: List[str]
    ) -> str:
        """Generate human-readable gap analysis."""
        if not missing_skills:
            return "No significant skill gaps identified."

        analysis = f"Missing {len(missing_skills)} required skills: {', '.join(missing_skills[:5])}"
        if transferable:
            analysis += f". Transferable skills that may compensate: {', '.join(transferable[:3])}."

        return analysis

    def _generate_recommendation(
        self,
        overall: float,
        skills: float,
        experience: float,
        missing: List[str]
    ) -> str:
        """Generate actionable recommendation."""
        if overall >= 0.85:
            return "Strong match. Highly recommended to apply immediately."
        elif overall >= 0.70:
            if missing:
                return f"Good match with minor gaps in {', '.join(missing[:3])}. Consider addressing these in cover letter."
            return "Good match. Apply with confidence."
        elif overall >= 0.55:
            return "Moderate match. Apply if interested, but tailor resume to highlight relevant experience."
        else:
            return "Weak match. Consider only if strongly interested in company or role."

    async def generate_customization(
        self,
        profile: Dict,
        job: Dict,
        match_data: Dict
    ) -> Dict[str, Any]:
        """
        Generate AI-customized application materials.
        """
        # Generate tailored resume bullets
        tailored_bullets = await self._tailor_resume_bullets(
            profile.get("experience", []),
            job,
            match_data["matching_skills"]
        )

        # Generate cover letter
        cover_letter = await self._generate_cover_letter(profile, job, match_data)

        # Generate screening answers
        screening_answers = await self._generate_screening_answers(profile, job)

        # Extract ATS keywords
        ats_keywords = self._extract_ats_keywords(job)

        return {
            "tailored_resume_bullets": tailored_bullets,
            "generated_cover_letter": cover_letter,
            "screening_answers": screening_answers,
            "ats_keywords": ats_keywords,
            "why_company": await self._generate_why_company(profile, job),
            "why_role": await self._generate_why_role(profile, job, match_data)
        }

    async def _tailor_resume_bullets(
        self,
        experiences: List[Dict],
        job: Dict,
        matching_skills: List[str]
    ) -> Dict[str, str]:
        """Rewrite experience bullets to emphasize relevant skills."""
        tailored = {}

        for exp in experiences[:3]:  # Top 3 experiences
            original_bullets = exp.get("achievements", [exp.get("description", "")])
            company = exp.get("company", "Company")

            prompt = f"""
            Rewrite these resume bullets to emphasize skills relevant to this job.

            Job: {job.get("title", "")} at {job.get("company", "")}
            Key Skills to Emphasize: {', '.join(matching_skills[:8])}

            Original Bullets:
            {chr(10).join(f"- {b}" for b in original_bullets[:3])}

            Rules:
            - Keep same factual content
            - Use strong action verbs
            - Include relevant keywords naturally
            - Quantify where possible
            - Max 2 bullets, 1-2 lines each

            Return ONLY the rewritten bullets, one per line starting with "- ".
            """

            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=300
                )
                tailored[company] = response.choices[0].message.content
            except:
                tailored[company] = "\n".join(original_bullets[:2])

        return tailored

    async def _generate_cover_letter(
        self,
        profile: Dict,
        job: Dict,
        match_data: Dict
    ) -> str:
        """Generate personalized cover letter."""
        prompt = f"""
        Write a compelling, concise cover letter (250-350 words) for this candidate applying to this job.

        Candidate: {profile.get("name", "Candidate")}
        Current Title: {profile.get("title", "")}
        Key Skills: {', '.join(profile.get("skills", [])[:10])}
        Experience: {profile.get("years_of_experience", 0)} years
        Summary: {profile.get("summary", "")[:300]}

        Job: {job.get("title", "")} at {job.get("company", "")}
        Description: {job.get("description", "")[:800]}

        Match Strengths: {', '.join(match_data.get("matching_skills", [])[:5])}

        Rules:
        - Show genuine enthusiasm for the company
        - Connect specific experience to job requirements
        - Mention 2-3 specific achievements
        - Professional but personable tone
        - No generic fluff
        - End with clear call to action
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=600
            )
            return response.choices[0].message.content
        except:
            return "Cover letter generation failed. Please write manually."

    async def _generate_screening_answers(
        self,
        profile: Dict,
        job: Dict
    ) -> Dict[str, str]:
        """Generate answers for common screening questions."""
        common_questions = {
            "why_this_company": f"Why do you want to work at {job.get('company', 'this company')}?",
            "why_this_role": f"Why are you interested in the {job.get('title', 'this role')} position?",
            "salary_expectations": "What are your salary expectations?",
            "notice_period": "What is your notice period?",
            "work_authorization": "Are you authorized to work in this location?",
            "relocation": "Are you willing to relocate?",
            "remote_experience": "Do you have experience working remotely?",
        }

        answers = {}

        for key, question in common_questions.items():
            prompt = f"""
            Generate a brief, professional answer (1-2 sentences) to this screening question.

            Question: {question}

            Candidate: {profile.get("name", "")}
            Title: {profile.get("title", "")}
            Location: {profile.get("location", "")}
            Salary Min: {profile.get("min_salary", "Not specified")}
            Notice Period: {profile.get("notice_period_days", 30)} days
            Work Mode Pref: {profile.get("work_mode_preference", "remote")}

            Rules:
            - Be honest and specific
            - Match the candidate's profile
            - Professional tone
            - Brief but complete
            """

            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=100
                )
                answers[key] = response.choices[0].message.content
            except:
                answers[key] = "Please answer manually."

        return answers

    def _extract_ats_keywords(self, job: Dict) -> List[str]:
        """Extract important ATS keywords from job description."""
        desc = job.get("description", "").lower()

        # Common ATS keywords for tech/AI roles
        ats_pool = [
            "python", "machine learning", "deep learning", "tensorflow", "pytorch",
            "sql", "aws", "docker", "kubernetes", "ci/cd", "agile", "scrum",
            "data analysis", "nlp", "computer vision", "llm", "api", "rest",
            "graphql", "microservices", "cloud", "git", "linux", "pandas",
            "numpy", "spark", "hadoop", "kafka", "airflow", "dbt", "terraform",
            "prometheus", "grafana", "jupyter", "matplotlib", "seaborn",
            "statistics", "a/b testing", "experimentation", "product sense",
            "communication", "leadership", "collaboration", "problem solving"
        ]

        found = [kw for kw in ats_pool if kw in desc]
        return found[:15]  # Top 15

    async def _generate_why_company(self, profile: Dict, job: Dict) -> str:
        """Generate 'Why this company' answer."""
        prompt = f"""
        Write a 2-3 sentence answer to "Why do you want to work at {job.get('company', 'this company')}?"
        Based on: {profile.get('summary', '')[:200]}
        Be specific and genuine.
        """
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}],
                temperature=0.4, max_tokens=100
            )
            return response.choices[0].message.content
        except:
            return f"I admire {job.get('company', 'this company')}'s work and believe my skills align well with their mission."

    async def _generate_why_role(self, profile: Dict, job: Dict, match_data: Dict) -> str:
        """Generate 'Why this role' answer."""
        prompt = f"""
        Write a 2-3 sentence answer to "Why are you interested in this {job.get('title', 'role')}?"
        Candidate skills: {', '.join(profile.get('skills', [])[:5])}
        Matching skills: {', '.join(match_data.get('matching_skills', [])[:5])}
        """
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}],
                temperature=0.4, max_tokens=100
            )
            return response.choices[0].message.content
        except:
            return f"This role aligns perfectly with my experience in {', '.join(profile.get('skills', [])[:3])}."
