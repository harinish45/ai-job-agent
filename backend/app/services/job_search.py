"""
Smart Job Search Engine
Aggregates jobs from multiple sources, deduplicates, detects scams,
and finds hidden opportunities on company career pages.
"""
import asyncio
import hashlib
import re
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import httpx
from bs4 import BeautifulSoup
from app.config import get_settings
from app.core.celery_app import celery_app

settings = get_settings()

@dataclass
class JobSource:
    name: str
    base_url: str
    search_url_template: str
    requires_auth: bool = False
    is_api: bool = False

class JobSearchEngine:
    """
    Multi-source job aggregator with intelligent filtering.
    """

    SOURCES = [
        JobSource("linkedin", "https://www.linkedin.com",
                  "https://www.linkedin.com/jobs/search?keywords={keywords}&location={location}&f_WT={work_mode}"),
        JobSource("indeed", "https://www.indeed.com",
                  "https://www.indeed.com/jobs?q={keywords}&l={location}&remotejob={remote}"),
        JobSource("wellfound", "https://wellfound.com",
                  "https://wellfound.com/role/{keywords}"),
        JobSource("remoteok", "https://remoteok.com",
                  "https://remoteok.com/remote-{keywords}-jobs"),
        JobSource("weworkremotely", "https://weworkremotely.com",
                  "https://weworkremotely.com/remote-jobs/search?term={keywords}"),
        JobSource("arc_dev", "https://arc.dev",
                  "https://arc.dev/?keyword={keywords}"),
    ]

    AI_ROLE_PATTERNS = [
        r'\bprompt\s*engineer\b',
        r'\bai\s*ops\b',
        r'\bautomation\s*specialist\b',
        r'\bai\s*product\b',
        r'\bai\s*trainer\b',
        r'\bsafety\s*reviewer\b',
        r'\bdata\s*labeling\b',
        r'\bworkflow\s*automation\b',
        r'\bcybersecurity\s*ai\b',
        r'\bml\s*engineer\b',
        r'\bmachine\s*learning\b',
        r'\bdeep\s*learning\b',
        r'\bnlp\s*engineer\b',
        r'\bcomputer\s*vision\b',
        r'\bllm\b',
        r'\bgenai\b',
        r'\bai\s*research\b',
        r'\bai\s*strategist\b',
        r'\brobotics\b',
        r'\bautonomous\b',
    ]

    SCAM_INDICATORS = [
        r'\$\d{3,}/week\s*(?:guaranteed|easy)',
        r'(?:no\s*experience|no\s*skills)\s*(?:required|needed)',
        r'work\s*from\s*home\s*(?:and|&)\s*earn\s*\$\d+',
        r'(?:click\s*here|apply\s*now)\s*to\s*(?:get|receive)\s*(?:rich|money)',
        r'(?:crypto|bitcoin|forex)\s*(?:trading|investment)',
        r'(?:pay|send)\s*(?:us|me)\s*(?:first|upfront)',
        r'(?:whatsapp|telegram)\s*(?:only|contact)',
        r'(?:unlimited|unlimited)\s*(?:income|earnings)',
    ]

    def __init__(self):
        self.seen_hashes = set()
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    async def search_all_sources(
        self,
        keywords: List[str],
        location: str = "",
        work_mode: str = "remote",
        experience_level: str = "mid",
        max_results_per_source: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search across all configured sources concurrently.
        """
        all_jobs = []

        # Build search queries
        query = " ".join(keywords)

        # Search all sources concurrently
        tasks = []
        for source in self.SOURCES:
            task = self._search_source(
                source, query, location, work_mode,
                experience_level, max_results_per_source
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)

        # Deduplicate
        unique_jobs = self._deduplicate_jobs(all_jobs)

        # Scam detection
        clean_jobs = self._filter_scams(unique_jobs)

        # AI role detection
        for job in clean_jobs:
            job["is_ai_role"] = self._detect_ai_role(job)
            if job["is_ai_role"]:
                job["ai_role_category"] = self._categorize_ai_role(job)

        return clean_jobs

    async def _search_source(
        self,
        source: JobSource,
        query: str,
        location: str,
        work_mode: str,
        experience_level: str,
        max_results: int
    ) -> List[Dict]:
        """Search a single job source."""
        try:
            if source.name == "linkedin":
                return await self._scrape_linkedin(query, location, work_mode, max_results)
            elif source.name == "indeed":
                return await self._scrape_indeed(query, location, work_mode, max_results)
            elif source.name == "wellfound":
                return await self._scrape_wellfound(query, max_results)
            elif source.name == "remoteok":
                return await self._scrape_remoteok(query, max_results)
            elif source.name == "weworkremotely":
                return await self._scrape_weworkremotely(query, max_results)
            else:
                return []
        except Exception as e:
            print(f"Error searching {source.name}: {e}")
            return []

    async def _scrape_linkedin(
        self, query: str, location: str, work_mode: str, max_results: int
    ) -> List[Dict]:
        """Scrape LinkedIn job listings."""
        jobs = []

        # LinkedIn uses different work mode codes
        wt_map = {"remote": "2", "hybrid": "3", "onsite": "1"}
        wt = wt_map.get(work_mode, "")

        url = f"https://www.linkedin.com/jobs/search?keywords={query.replace(' ', '%20')}&location={location.replace(' ', '%20')}&f_WT={wt}"

        try:
            response = await self.http_client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            job_cards = soup.find_all('div', class_='base-card')

            for card in job_cards[:max_results]:
                try:
                    title_elem = card.find('h3', class_='base-search-card__title')
                    company_elem = card.find('h4', class_='base-search-card__subtitle')
                    location_elem = card.find('span', class_='job-search-card__location')
                    link_elem = card.find('a', class_='base-card__full-link')

                    if not title_elem or not company_elem:
                        continue

                    job = {
                        "source_platform": "linkedin",
                        "title": title_elem.text.strip(),
                        "company": company_elem.text.strip(),
                        "location": location_elem.text.strip() if location_elem else "",
                        "source_url": link_elem['href'] if link_elem else "",
                        "apply_url": link_elem['href'] if link_elem else "",
                        "apply_method": "direct_link",
                        "description": "",  # Would need detail page scrape
                        "discovered_at": datetime.utcnow().isoformat(),
                    }
                    jobs.append(job)
                except Exception:
                    continue
        except Exception as e:
            print(f"LinkedIn scrape error: {e}")

        return jobs

    async def _scrape_indeed(
        self, query: str, location: str, work_mode: str, max_results: int
    ) -> List[Dict]:
        """Scrape Indeed job listings."""
        jobs = []
        remote_flag = "1" if work_mode == "remote" else ""

        url = f"https://www.indeed.com/jobs?q={query.replace(' ', '+')}&l={location.replace(' ', '+')}&remotejob={remote_flag}"

        try:
            response = await self.http_client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            job_cards = soup.find_all('div', class_='job_seen_beacon')

            for card in job_cards[:max_results]:
                try:
                    title_elem = card.find('h2', class_='jobTitle')
                    company_elem = card.find('span', class_='companyName')
                    location_elem = card.find('div', class_='companyLocation')
                    link_elem = card.find('a', class_='jcs-JobTitle')

                    job = {
                        "source_platform": "indeed",
                        "title": title_elem.text.strip() if title_elem else "",
                        "company": company_elem.text.strip() if company_elem else "",
                        "location": location_elem.text.strip() if location_elem else "",
                        "source_url": f"https://indeed.com{link_elem['href']}" if link_elem else "",
                        "apply_url": f"https://indeed.com{link_elem['href']}" if link_elem else "",
                        "apply_method": "direct_link",
                        "description": "",
                        "discovered_at": datetime.utcnow().isoformat(),
                    }
                    jobs.append(job)
                except Exception:
                    continue
        except Exception as e:
            print(f"Indeed scrape error: {e}")

        return jobs

    async def _scrape_wellfound(self, query: str, max_results: int) -> List[Dict]:
        """Scrape Wellfound (AngelList) startup jobs."""
        jobs = []
        url = f"https://wellfound.com/role/{query.replace(' ', '-')}"

        try:
            response = await self.http_client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            job_cards = soup.find_all('div', class_='styles_jobListing__')

            for card in job_cards[:max_results]:
                try:
                    title_elem = card.find('h2')
                    company_elem = card.find('span', class_='styles_company__')
                    link_elem = card.find('a')

                    job = {
                        "source_platform": "wellfound",
                        "title": title_elem.text.strip() if title_elem else "",
                        "company": company_elem.text.strip() if company_elem else "",
                        "location": "Remote/Startup",
                        "source_url": f"https://wellfound.com{link_elem['href']}" if link_elem else "",
                        "apply_url": f"https://wellfound.com{link_elem['href']}" if link_elem else "",
                        "apply_method": "direct_link",
                        "description": "",
                        "discovered_at": datetime.utcnow().isoformat(),
                    }
                    jobs.append(job)
                except Exception:
                    continue
        except Exception as e:
            print(f"Wellfound scrape error: {e}")

        return jobs

    async def _scrape_remoteok(self, query: str, max_results: int) -> List[Dict]:
        """Scrape RemoteOK listings."""
        jobs = []
        url = f"https://remoteok.com/remote-{query.replace(' ', '-')}-jobs"

        try:
            response = await self.http_client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            job_rows = soup.find_all('tr', class_='job')

            for row in job_rows[:max_results]:
                try:
                    title_elem = row.find('h2', class_='company_and_position')
                    company_elem = row.find('h3')
                    link_elem = row.find('a', class_='preventLink')

                    job = {
                        "source_platform": "remoteok",
                        "title": title_elem.text.strip() if title_elem else "",
                        "company": company_elem.text.strip() if company_elem else "",
                        "location": "Remote",
                        "source_url": link_elem['href'] if link_elem else "",
                        "apply_url": link_elem['href'] if link_elem else "",
                        "apply_method": "direct_link",
                        "description": "",
                        "discovered_at": datetime.utcnow().isoformat(),
                    }
                    jobs.append(job)
                except Exception:
                    continue
        except Exception as e:
            print(f"RemoteOK scrape error: {e}")

        return jobs

    async def _scrape_weworkremotely(self, query: str, max_results: int) -> List[Dict]:
        """Scrape We Work Remotely listings."""
        jobs = []
        url = f"https://weworkremotely.com/remote-jobs/search?term={query.replace(' ', '+')}"

        try:
            response = await self.http_client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            job_listings = soup.find_all('li', class_='feature')

            for listing in job_listings[:max_results]:
                try:
                    link_elem = listing.find('a')
                    title_elem = listing.find('span', class_='title')
                    company_elem = listing.find('span', class_='company')

                    job = {
                        "source_platform": "weworkremotely",
                        "title": title_elem.text.strip() if title_elem else "",
                        "company": company_elem.text.strip() if company_elem else "",
                        "location": "Remote",
                        "source_url": f"https://weworkremotely.com{link_elem['href']}" if link_elem else "",
                        "apply_url": f"https://weworkremotely.com{link_elem['href']}" if link_elem else "",
                        "apply_method": "direct_link",
                        "description": "",
                        "discovered_at": datetime.utcnow().isoformat(),
                    }
                    jobs.append(job)
                except Exception:
                    continue
        except Exception as e:
            print(f"WWR scrape error: {e}")

        return jobs

    async def search_company_career_pages(
        self,
        company_list: List[str],
        keywords: List[str]
    ) -> List[Dict]:
        """
        Find hidden jobs on company career pages before they hit job boards.
        """
        jobs = []

        for company in company_list:
            try:
                # Common career page patterns
                career_urls = [
                    f"https://{company.lower().replace(' ', '')}.com/careers",
                    f"https://{company.lower().replace(' ', '')}.com/jobs",
                    f"https://boards.greenhouse.io/{company.lower().replace(' ', '')}",
                    f"https://jobs.lever.co/{company.lower().replace(' ', '')}",
                    f"https://{company.lower().replace(' ', '')}.workable.com",
                ]

                for url in career_urls:
                    try:
                        response = await self.http_client.get(url, timeout=10)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.text, 'html.parser')

                            # Look for job listings
                            job_links = soup.find_all('a', href=re.compile(r'job|position|opening'))

                            for link in job_links[:10]:
                                title = link.text.strip()
                                if any(kw.lower() in title.lower() for kw in keywords):
                                    href = link.get('href', '')
                                    if not href.startswith('http'):
                                        href = url.rstrip('/') + '/' + href.lstrip('/')

                                    jobs.append({
                                        "source_platform": "company_career_page",
                                        "title": title,
                                        "company": company,
                                        "location": "",
                                        "source_url": url,
                                        "apply_url": href,
                                        "apply_method": "direct_link",
                                        "description": "",
                                        "discovered_at": datetime.utcnow().isoformat(),
                                        "is_hidden_job": True,
                                    })
                    except:
                        continue
            except Exception as e:
                print(f"Company search error for {company}: {e}")

        return jobs

    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs using content hashing."""
        unique = []
        seen = set()

        for job in jobs:
            # Create hash from title + company + location
            hash_content = f"{job.get('title', '')}|{job.get('company', '')}|{job.get('location', '')}"
            job_hash = hashlib.md5(hash_content.encode()).hexdigest()

            if job_hash not in seen:
                seen.add(job_hash)
                job["content_hash"] = job_hash
                unique.append(job)

        return unique

    def _filter_scams(self, jobs: List[Dict]) -> List[Dict]:
        """Detect and filter scam job listings."""
        clean = []

        for job in jobs:
            text_to_check = f"{job.get('title', '')} {job.get('description', '')}".lower()
            is_scam = False
            scam_reason = ""

            for pattern in self.SCAM_INDICATORS:
                if re.search(pattern, text_to_check):
                    is_scam = True
                    scam_reason = f"Matched scam pattern: {pattern}"
                    break

            # Additional heuristics
            if not is_scam:
                # Check for unrealistic pay
                pay_match = re.search(r'\$?(\d{2,3}),(\d{3})\s*(?:per\s*week|/week)', text_to_check)
                if pay_match:
                    weekly = int(pay_match.group(1) + pay_match.group(2))
                    if weekly > 5000:  # > $260k/year advertised as weekly
                        is_scam = True
                        scam_reason = "Unrealistic weekly pay"

                # Check for missing company info
                if not job.get('company') or job.get('company') in ['', 'Confidential']:
                    if 'work from home' in text_to_check and 'easy' in text_to_check:
                        is_scam = True
                        scam_reason = "Vague company + WFH + easy money language"

            job["is_scam_flagged"] = is_scam
            job["scam_reason"] = scam_reason if is_scam else ""

            if not is_scam:
                clean.append(job)

        return clean

    def _detect_ai_role(self, job: Dict) -> bool:
        """Detect if job is an AI-related role."""
        text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        return any(re.search(pattern, text) for pattern in self.AI_ROLE_PATTERNS)

    def _categorize_ai_role(self, job: Dict) -> str:
        """Categorize AI role into specific type."""
        title = job.get('title', '').lower()
        desc = job.get('description', '').lower()
        text = f"{title} {desc}"

        categories = {
            "prompt_engineer": ["prompt", "prompting", "instruction tuning"],
            "ml_engineer": ["ml engineer", "machine learning engineer", "mlops"],
            "ai_researcher": ["research scientist", "ai researcher", "research engineer"],
            "ai_product": ["ai product", "product manager ai", "ai strategist"],
            "data_scientist": ["data scientist", "analytics", "statistical"],
            "ai_ops": ["ai infrastructure", "ml platform", "ai operations"],
            "ai_safety": ["safety", "alignment", "rlhf", "red team"],
            "automation": ["automation engineer", "rpa", "workflow"],
            "nlp_engineer": ["nlp", "natural language", "llm engineer"],
            "cv_engineer": ["computer vision", "cv engineer", "perception"],
        }

        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category

        return "general_ai"


@celery_app.task(bind=True, max_retries=3)
def daily_job_search(self, user_id: int):
    """Celery task for daily job search."""
    import asyncio
    from app.models.database import SessionLocal
    from app.models.models import UserProfile, JobListing

    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not profile:
            return {"error": "Profile not found"}

        engine = JobSearchEngine()

        keywords = profile.target_roles or ["software engineer"]
        location = profile.location or ""
        work_mode = profile.work_mode_preference.value if profile.work_mode_preference else "remote"

        # Run search
        jobs = asyncio.run(engine.search_all_sources(
            keywords=keywords,
            location=location,
            work_mode=work_mode,
            experience_level=profile.experience_level.value if profile.experience_level else "mid"
        ))

        # Also search company career pages for target companies
        # This would come from user's target company list

        # Save to database
        saved_count = 0
        for job_data in jobs:
            # Check if already exists
            existing = db.query(JobListing).filter(
                JobListing.source_url == job_data["source_url"]
            ).first()

            if not existing:
                job = JobListing(**job_data)
                db.add(job)
                saved_count += 1

        db.commit()

        return {
            "status": "success",
            "jobs_found": len(jobs),
            "jobs_saved": saved_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=300)
    finally:
        db.close()
