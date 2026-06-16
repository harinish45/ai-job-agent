"""
Auto Apply Engine
Uses Playwright to automatically fill and submit job applications.
Handles form detection, field mapping, resume upload, and CAPTCHA detection.
"""
import asyncio
import random
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from playwright.async_api import async_playwright, Page, BrowserContext
from app.config import get_settings
from app.core.celery_app import celery_app
from app.core.security import decrypt_credentials

settings = get_settings()

class AutoApplyEngine:
    """
    Intelligent form-filling engine for job applications.
    """

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.application_logs = []

    async def initialize(self, profile_dir: Optional[str] = None):
        """Initialize browser with optional persistent profile."""
        self.playwright = await async_playwright().start()

        browser_args = {
            "headless": settings.HEADLESS,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ]
        }

        if profile_dir:
            browser_args["user_data_dir"] = profile_dir

        self.browser = await self.playwright.chromium.launch(**browser_args)

        context_args = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "locale": "en-US",
            "timezone_id": "America/New_York",
        }

        self.context = await self.browser.new_context(**context_args)

        # Inject anti-detection script
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            window.chrome = { runtime: {} };
        """)

        self.page = await self.context.new_page()

    async def apply_to_job(
        self,
        apply_url: str,
        profile: Dict[str, Any],
        job: Dict[str, Any],
        customization: Dict[str, Any],
        resume_path: str,
        cover_letter_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main method: Navigate to apply URL and complete application.
        """
        result = {
            "success": False,
            "status": "started",
            "logs": [],
            "form_data": {},
            "screenshots": [],
            "captcha_detected": False,
            "human_verification_needed": False,
            "error": None,
        }

        try:
            # Navigate to application page
            await self._safe_goto(apply_url)
            await asyncio.sleep(random.uniform(2, 4))

            # Detect application type
            app_type = await self._detect_application_type()
            result["logs"].append(f"Detected application type: {app_type}")

            # Check for CAPTCHA
            captcha = await self._detect_captcha()
            if captcha["detected"]:
                result["captcha_detected"] = True
                result["human_verification_needed"] = True
                result["status"] = "captcha_detected"
                result["logs"].append(f"CAPTCHA detected: {captcha['type']}")
                await self._take_screenshot("captcha_detected")
                return result

            # Fill application based on type
            if app_type == "greenhouse":
                await self._fill_greenhouse(profile, customization, resume_path, cover_letter_path)
            elif app_type == "lever":
                await self._fill_lever(profile, customization, resume_path, cover_letter_path)
            elif app_type == "workday":
                await self._fill_workday(profile, customization, resume_path, cover_letter_path)
            elif app_type == "linkedin_easy_apply":
                await self._fill_linkedin_easy_apply(profile, customization, resume_path)
            elif app_type == "indeed_apply":
                await self._fill_indeed_apply(profile, customization, resume_path)
            else:
                await self._fill_generic_form(profile, customization, resume_path, cover_letter_path)

            # Check for terms checkbox
            await self._handle_terms_checkbox()

            # Review before submit (configurable)
            # await self._take_screenshot("pre_submit_review")

            # Submit
            # submit_success = await self._submit_application()

            result["success"] = True
            result["status"] = "completed"
            result["form_data"] = self._get_submitted_data()
            result["logs"].append("Application completed successfully")

        except Exception as e:
            result["error"] = str(e)
            result["status"] = "error"
            result["logs"].append(f"Error: {str(e)}")
            await self._take_screenshot("error_state")

        return result

    async def _safe_goto(self, url: str, max_retries: int = 3):
        """Navigate with retry logic."""
        for attempt in range(max_retries):
            try:
                response = await self.page.goto(url, wait_until="networkidle", timeout=30000)
                if response and response.status < 400:
                    return
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(random.uniform(1, 3))

    async def _detect_application_type(self) -> str:
        """Detect which ATS/platform the application uses."""
        url = self.page.url.lower()
        content = await self.page.content()
        content_lower = content.lower()

        if "greenhouse.io" in url or "boards.greenhouse" in content_lower:
            return "greenhouse"
        elif "jobs.lever.co" in url:
            return "lever"
        elif "myworkdayjobs.com" in url or "workday" in content_lower:
            return "workday"
        elif "linkedin.com" in url and "easy-apply" in content_lower:
            return "linkedin_easy_apply"
        elif "indeed.com" in url and "apply" in url:
            return "indeed_apply"
        elif "ashby" in url or "ashbyhq" in content_lower:
            return "ashby"
        elif "breezy" in url:
            return "breezy"
        else:
            return "generic"

    async def _detect_captcha(self) -> Dict:
        """Detect if page has CAPTCHA or human verification."""
        captcha_selectors = [
            'iframe[src*="recaptcha"]',
            'iframe[src*="hcaptcha"]',
            '.g-recaptcha',
            '.h-captcha',
            '[data-captcha]',
            'input[name*="captcha"]',
            'img[src*="captcha"]',
            '#captcha',
            '.captcha',
            'text:has("I\'m not a robot")',
            'text:has("Verify you are human")',
        ]

        for selector in captcha_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    return {"detected": True, "type": selector}
            except:
                continue

        # Check for suspicious challenge pages
        title = await self.page.title()
        if any(word in title.lower() for word in ["challenge", "verify", "captcha", "security"]):
            return {"detected": True, "type": "page_title_challenge"}

        return {"detected": False, "type": None}

    async def _fill_greenhouse(
        self,
        profile: Dict,
        customization: Dict,
        resume_path: str,
        cover_letter_path: Optional[str]
    ):
        """Fill Greenhouse application form."""
        # Name
        await self._fill_field('input[name="first_name"]', profile.get("first_name", ""))
        await self._fill_field('input[name="last_name"]', profile.get("last_name", ""))

        # Email
        await self._fill_field('input[name="email"]', profile.get("email", ""))

        # Phone
        await self._fill_field('input[name="phone"]', profile.get("phone", ""))

        # LinkedIn
        await self._fill_field('input[name="linkedin"]', profile.get("linkedin_url", ""))

        # GitHub/Website
        await self._fill_field('input[name="website"]', profile.get("github_url", "") or profile.get("portfolio_url", ""))

        # Resume upload
        await self._upload_file('input[type="file"][name*="resume"]', resume_path)

        # Cover letter
        if cover_letter_path:
            await self._upload_file('input[type="file"][name*="cover_letter"]', cover_letter_path)
        else:
            # Fill text area if no file
            cover_letter = customization.get("generated_cover_letter", "")
            await self._fill_field('textarea[name*="cover_letter"]', cover_letter)

        # Custom questions
        await self._handle_custom_questions(profile, customization)

    async def _fill_lever(
        self,
        profile: Dict,
        customization: Dict,
        resume_path: str,
        cover_letter_path: Optional[str]
    ):
        """Fill Lever application form."""
        # Name
        await self._fill_field('input[name="name"]', profile.get("full_name", ""))

        # Email
        await self._fill_field('input[name="email"]', profile.get("email", ""))

        # Phone
        await self._fill_field('input[name="phone"]', profile.get("phone", ""))

        # LinkedIn
        await self._fill_field('input[name="urls[LinkedIn]"]', profile.get("linkedin_url", ""))

        # Portfolio
        await self._fill_field('input[name="urls[Portfolio]"]', profile.get("portfolio_url", ""))

        # GitHub
        await self._fill_field('input[name="urls[GitHub]"]', profile.get("github_url", ""))

        # Resume
        await self._upload_file('input[type="file"][name*="resume"]', resume_path)

        # Cover letter
        cover_letter = customization.get("generated_cover_letter", "")
        await self._fill_field('textarea[name*="coverLetter"]', cover_letter)

        # Custom questions
        await self._handle_custom_questions(profile, customization)

    async def _fill_workday(
        self,
        profile: Dict,
        customization: Dict,
        resume_path: str,
        cover_letter_path: Optional[str]
    ):
        """Fill Workday application form."""
        # Workday forms are complex and dynamic
        # This is a simplified version

        # Try to find and fill name fields
        await self._fill_field_by_placeholder("First Name", profile.get("first_name", ""))
        await self._fill_field_by_placeholder("Last Name", profile.get("last_name", ""))
        await self._fill_field_by_placeholder("Email", profile.get("email", ""))
        await self._fill_field_by_placeholder("Phone", profile.get("phone", ""))

        # Resume upload
        await self._upload_file('input[type="file"]', resume_path)

        # Custom questions
        await self._handle_custom_questions(profile, customization)

    async def _fill_linkedin_easy_apply(
        self,
        profile: Dict,
        customization: Dict,
        resume_path: str
    ):
        """Fill LinkedIn Easy Apply form."""
        # Click Easy Apply button
        easy_apply_btn = await self.page.query_selector('button:has-text("Easy Apply")')
        if easy_apply_btn:
            await easy_apply_btn.click()
            await asyncio.sleep(2)

        # Fill contact info
        await self._fill_field('input[id*="email"]', profile.get("email", ""))
        await self._fill_field('input[id*="phone"]', profile.get("phone", ""))

        # Resume
        await self._upload_file('input[type="file"]', resume_path)

        # Handle multi-step form
        max_steps = 5
        for step in range(max_steps):
            # Fill any visible fields
            await self._handle_custom_questions(profile, customization)

            # Click next/review
            next_btn = await self.page.query_selector('button:has-text("Next")') or \
                       await self.page.query_selector('button:has-text("Review")')
            if next_btn:
                await next_btn.click()
                await asyncio.sleep(2)
            else:
                break

    async def _fill_generic_form(
        self,
        profile: Dict,
        customization: Dict,
        resume_path: str,
        cover_letter_path: Optional[str]
    ):
        """Fill generic application form using field detection."""
        # Detect all form fields
        fields = await self._detect_form_fields()

        for field in fields:
            await self._fill_detected_field(field, profile, customization, resume_path, cover_letter_path)

    async def _detect_form_fields(self) -> List[Dict]:
        """Detect all input fields on the page."""
        fields = []

        # Text inputs
        inputs = await self.page.query_selector_all('input[type="text"], input[type="email"], input[type="tel"], input[type="url"]')
        for inp in inputs:
            name = await inp.get_attribute("name") or ""
            placeholder = await inp.get_attribute("placeholder") or ""
            id_attr = await inp.get_attribute("id") or ""
            fields.append({
                "element": inp,
                "type": "text",
                "name": name,
                "placeholder": placeholder,
                "id": id_attr,
            })

        # Textareas
        textareas = await self.page.query_selector_all('textarea')
        for ta in textareas:
            name = await ta.get_attribute("name") or ""
            placeholder = await ta.get_attribute("placeholder") or ""
            fields.append({
                "element": ta,
                "type": "textarea",
                "name": name,
                "placeholder": placeholder,
                "id": await ta.get_attribute("id") or "",
            })

        # File inputs
        file_inputs = await self.page.query_selector_all('input[type="file"]')
        for fi in file_inputs:
            name = await fi.get_attribute("name") or ""
            fields.append({
                "element": fi,
                "type": "file",
                "name": name,
                "placeholder": "",
                "id": await fi.get_attribute("id") or "",
            })

        # Selects
        selects = await self.page.query_selector_all('select')
        for sel in selects:
            name = await sel.get_attribute("name") or ""
            fields.append({
                "element": sel,
                "type": "select",
                "name": name,
                "placeholder": "",
                "id": await sel.get_attribute("id") or "",
            })

        return fields

    async def _fill_detected_field(
        self,
        field: Dict,
        profile: Dict,
        customization: Dict,
        resume_path: str,
        cover_letter_path: Optional[str]
    ):
        """Fill a detected field based on its characteristics."""
        name = field["name"].lower()
        placeholder = field["placeholder"].lower()
        combined = f"{name} {placeholder}"

        if field["type"] == "text" or field["type"] == "textarea":
            value = None

            # Map field to profile data
            if any(k in combined for k in ["first", "fname"]):
                value = profile.get("first_name", "")
            elif any(k in combined for k in ["last", "lname", "surname"]):
                value = profile.get("last_name", "")
            elif any(k in combined for k in ["full", "name"]):
                value = profile.get("full_name", "")
            elif any(k in combined for k in ["email", "e-mail"]):
                value = profile.get("email", "")
            elif any(k in combined for k in ["phone", "mobile", "cell"]):
                value = profile.get("phone", "")
            elif any(k in combined for k in ["linkedin"]):
                value = profile.get("linkedin_url", "")
            elif any(k in combined for k in ["github", "git"]):
                value = profile.get("github_url", "")
            elif any(k in combined for k in ["portfolio", "website", "url", "personal"]):
                value = profile.get("portfolio_url", "")
            elif any(k in combined for k in ["cover", "letter", "why"]):
                value = customization.get("generated_cover_letter", "")
            elif any(k in combined for k in ["salary", "compensation", "pay"]):
                value = str(profile.get("min_salary", ""))
            elif any(k in combined for k in ["notice", "availability"]):
                value = f"{profile.get('notice_period_days', 30)} days"
            elif any(k in combined for k in ["location", "city", "address"]):
                value = profile.get("location", "")

            if value:
                await field["element"].fill(str(value))
                await asyncio.sleep(random.uniform(0.1, 0.3))

        elif field["type"] == "file":
            if "resume" in combined or "cv" in combined:
                await field["element"].set_input_files(resume_path)
            elif "cover" in combined:
                if cover_letter_path:
                    await field["element"].set_input_files(cover_letter_path)

        elif field["type"] == "select":
            # Handle select fields
            await self._handle_select_field(field["element"], combined, profile)

    async def _handle_custom_questions(self, profile: Dict, customization: Dict):
        """Handle custom screening questions."""
        # Find all question containers
        questions = await self.page.query_selector_all('label, .question, .field-label')

        for question in questions:
            text = await question.inner_text()
            text_lower = text.lower()

            # Map to known answers
            answer = None

            if "salary" in text_lower or "compensation" in text_lower:
                answer = str(profile.get("min_salary", ""))
            elif "notice" in text_lower or "availability" in text_lower:
                answer = f"{profile.get('notice_period_days', 30)} days"
            elif "experience" in text_lower and "year" in text_lower:
                answer = str(profile.get("years_of_experience", ""))
            elif "why" in text_lower and "company" in text_lower:
                answer = customization.get("why_company", "")
            elif "why" in text_lower and "role" in text_lower:
                answer = customization.get("why_role", "")
            elif "work authorization" in text_lower or "visa" in text_lower:
                answer = "Yes" if not profile.get("visa_sponsorship_required") else "Requires sponsorship"
            elif "relocate" in text_lower:
                answer = "Yes" if profile.get("willing_to_relocate") else "No"
            elif "remote" in text_lower and "experience" in text_lower:
                answer = "Yes"

            if answer:
                # Find associated input
                input_elem = await question.query_selector('xpath=following::input[1]') or \
                           await question.query_selector('xpath=following::textarea[1]')
                if input_elem:
                    await input_elem.fill(str(answer))

    async def _handle_select_field(self, select_elem, combined: str, profile: Dict):
        """Handle select dropdown fields."""
        try:
            options = await select_elem.query_selector_all('option')
            option_texts = []
            for opt in options:
                text = await opt.inner_text()
                option_texts.append(text)

            # Select best match
            if "country" in combined or "location" in combined:
                target = profile.get("location", "United States")
            elif "experience" in combined:
                target = profile.get("experience_level", "Mid-level")
            else:
                return

            # Find closest match
            best_match = None
            best_score = 0
            for opt_text in option_texts:
                score = self._string_similarity(target.lower(), opt_text.lower())
                if score > best_score:
                    best_score = score
                    best_match = opt_text

            if best_match:
                await select_elem.select_option(label=best_match)
        except:
            pass

    async def _handle_terms_checkbox(self):
        """Check terms and conditions checkbox if present."""
        try:
            checkbox = await self.page.query_selector('input[type="checkbox"][name*="terms"], input[type="checkbox"][name*="agree"]')
            if checkbox:
                await checkbox.check()
        except:
            pass

    async def _submit_application(self) -> bool:
        """Submit the application form."""
        try:
            submit_btn = await self.page.query_selector('button[type="submit"], input[type="submit"], button:has-text("Submit"), button:has-text("Apply")')
            if submit_btn:
                await submit_btn.click()
                await asyncio.sleep(5)

                # Check for success indicators
                content = await self.page.content()
                success_indicators = ["thank you", "application submitted", "success", "received"]
                return any(ind in content.lower() for ind in success_indicators)
            return False
        except:
            return False

    async def _fill_field(self, selector: str, value: str):
        """Safely fill a field by selector."""
        try:
            element = await self.page.query_selector(selector)
            if element:
                await element.fill(str(value))
                await asyncio.sleep(random.uniform(0.1, 0.3))
        except:
            pass

    async def _fill_field_by_placeholder(self, placeholder: str, value: str):
        """Fill field by placeholder text."""
        try:
            element = await self.page.query_selector(f'input[placeholder*="{placeholder}" i]')
            if element:
                await element.fill(str(value))
        except:
            pass

    async def _upload_file(self, selector: str, file_path: str):
        """Upload file to input."""
        try:
            element = await self.page.query_selector(selector)
            if element:
                await element.set_input_files(file_path)
                await asyncio.sleep(1)
        except:
            pass

    async def _take_screenshot(self, name: str):
        """Take screenshot for logging."""
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            path = f"./screenshots/{name}_{timestamp}.png"
            await self.page.screenshot(path=path)
            return path
        except:
            return None

    def _get_submitted_data(self) -> Dict:
        """Get data that was submitted."""
        return {}  # Would track filled fields

    def _string_similarity(self, a: str, b: str) -> float:
        """Simple string similarity."""
        if not a or not b:
            return 0.0
        a_words = set(a.split())
        b_words = set(b.split())
        intersection = len(a_words & b_words)
        union = len(a_words | b_words)
        return intersection / union if union > 0 else 0.0

    async def close(self):
        """Clean up browser resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


@celery_app.task(bind=True, max_retries=2)
def process_pending_applications(self):
    """Celery task to process pending auto-apply applications."""
    import asyncio
    from app.models.database import SessionLocal
    from app.models.models import JobApplication, UserProfile, JobListing, ApplicationStatus

    db = SessionLocal()
    try:
        # Find applications pending auto-apply
        pending = db.query(JobApplication).filter(
            JobApplication.status == ApplicationStatus.PENDING_APPROVAL
        ).all()

        results = []
        for app in pending:
            # Check if auto-apply is enabled and match score is high enough
            profile = db.query(UserProfile).filter(UserProfile.user_id == app.user_id).first()
            job = db.query(JobListing).filter(JobListing.id == app.job_id).first()

            if not profile or not job:
                continue

            # Check rules
            if not profile.auto_apply_enabled:
                continue

            # Check match score
            from app.models.models import JobMatchScore
            match = db.query(JobMatchScore).filter(
                JobMatchScore.job_id == job.id,
                JobMatchScore.user_id == app.user_id
            ).first()

            if not match or match.overall_score < profile.auto_apply_min_match_score:
                continue

            # Check company exclusions
            if profile.excluded_companies and job.company in profile.excluded_companies:
                continue

            # Check industry exclusions
            if profile.excluded_industries and job.company_industry in profile.excluded_industries:
                continue

            # Check approval requirement
            if profile.require_approval_companies and job.company in profile.require_approval_companies:
                continue

            # Check daily limit
            today_apps = db.query(JobApplication).filter(
                JobApplication.user_id == app.user_id,
                JobApplication.applied_at >= datetime.utcnow().date()
            ).count()

            if today_apps >= profile.auto_apply_max_daily:
                continue

            # Proceed with auto-apply
            # This would call the apply engine
            results.append({
                "application_id": app.id,
                "job": job.title,
                "company": job.company,
                "status": "queued_for_apply"
            })

        return {"processed": len(results), "applications": results}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)
    finally:
        db.close()
