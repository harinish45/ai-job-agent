"""
Auto-Apply Automation Runner Engine.
Playwright automation scaffolds for LinkedIn Easy Apply, Indeed, Greenhouse, Lever, and generic forms.
"""

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

from src.models import ApplicationRecord, ApplicationStatus, CustomizationResult, ResumeData

logger = logging.getLogger(__name__)


class AutoApplyError(Exception):
    """Raised when an auto-apply workflow encounters a failure."""
    pass


class AutoApplyEngine:
    """Automates form detection, field population, and submission on ATS platforms."""

    SELECTOR_FALLBACKS: Dict[str, List[str]] = {
        "first_name": [
            'input[name="first_name"]', 'input[id*="first_name"]', 'input[name*="firstName"]',
            'input[placeholder*="First Name" i]', 'input[aria-label*="First Name" i]'
        ],
        "last_name": [
            'input[name="last_name"]', 'input[id*="last_name"]', 'input[name*="lastName"]',
            'input[placeholder*="Last Name" i]', 'input[aria-label*="Last Name" i]'
        ],
        "full_name": [
            'input[name="name"]', 'input[name="full_name"]', 'input[id*="fullName"]',
            'input[placeholder*="Full Name" i]', 'input[aria-label*="Full Name" i]'
        ],
        "email": [
            'input[type="email"]', 'input[name="email"]', 'input[id*="email"]',
            'input[placeholder*="Email" i]', 'input[aria-label*="Email" i]'
        ],
        "phone": [
            'input[type="tel"]', 'input[name="phone"]', 'input[id*="phone"]',
            'input[placeholder*="Phone" i]', 'input[aria-label*="Phone" i]'
        ],
        "linkedin": [
            'input[name*="linkedin" i]', 'input[id*="linkedin" i]', 'input[placeholder*="LinkedIn" i]',
            'input[name="urls[LinkedIn]"]'
        ],
        "github": [
            'input[name*="github" i]', 'input[id*="github" i]', 'input[placeholder*="GitHub" i]',
            'input[name="urls[GitHub]"]'
        ],
        "resume_file": [
            'input[type="file"][name*="resume" i]', 'input[type="file"][id*="resume" i]',
            'input[type="file"][data-qa*="resume"]', 'input[type="file"]'
        ],
        "cover_letter_text": [
            'textarea[name*="cover" i]', 'textarea[id*="cover" i]', 'textarea[placeholder*="Cover Letter" i]'
        ],
        "submit_button": [
            'button[type="submit"]', 'input[type="submit"]', 'button:has-text("Submit Application")',
            'button:has-text("Submit")', 'button:has-text("Apply Now")'
        ]
    }

    def __init__(self, headless: bool = True, timeout_ms: int = 30000):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    async def initialize(self) -> None:
        """Start Playwright browser with anti-detection evasions."""
        if not HAS_PLAYWRIGHT:
            raise AutoApplyError("Playwright is not installed. Install with `pip install playwright`.")

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
        )

    async def close(self) -> None:
        """Gracefully release browser context and engine."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def apply(
        self,
        job_url: str,
        resume: ResumeData,
        customization: CustomizationResult,
        resume_pdf_path: Optional[str] = None,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """Navigate to job application, populate fields, and optionally submit."""
        if not self.context:
            await self.initialize()

        page = await self.context.new_page()
        result: Dict[str, Any] = {
            "success": False,
            "platform": "unknown",
            "fields_filled": [],
            "captcha_detected": False,
            "dry_run": dry_run,
            "logs": []
        }

        try:
            logger.info("Navigating to application URL: %s", job_url)
            result["logs"].append(f"Navigating to {job_url}")
            await page.goto(job_url, timeout=self.timeout_ms, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            platform = self.detect_platform(job_url, await page.content())
            result["platform"] = platform
            result["logs"].append(f"Detected ATS platform: {platform}")

            captcha = await self.detect_captcha(page)
            if captcha:
                result["captcha_detected"] = True
                result["logs"].append("CAPTCHA detected; human intervention needed.")
                logger.warning("CAPTCHA present on %s", job_url)
                return result

            # Populate fields based on detected platform
            fields = await self._fill_platform_form(page, platform, resume, customization, resume_pdf_path)
            result["fields_filled"] = fields

            if not dry_run:
                submitted = await self._submit_form(page)
                result["success"] = submitted
                result["logs"].append("Application submitted live." if submitted else "Submit button not triggered.")
            else:
                result["success"] = True
                result["logs"].append("Dry run completed: verified fields without final submission.")

        except Exception as exc:
            logger.error("Auto apply error on %s: %s", job_url, exc)
            result["logs"].append(f"Error: {exc}")
        finally:
            await page.close()

        return result

    def detect_platform(self, url: str, html_content: str) -> str:
        """Classify ATS platform from URL structure or DOM signatures."""
        url_lower = url.lower()
        html_lower = html_content.lower()

        if "greenhouse.io" in url_lower or "boards.greenhouse" in html_lower:
            return "greenhouse"
        elif "lever.co" in url_lower or "jobs.lever" in html_lower:
            return "lever"
        elif "linkedin.com" in url_lower:
            return "linkedin_easy_apply"
        elif "indeed.com" in url_lower:
            return "indeed"
        elif "workday" in url_lower or "myworkdayjobs" in url_lower:
            return "workday"
        return "generic"

    async def detect_captcha(self, page: Page) -> bool:
        """Scan for Google reCAPTCHA, hCaptcha, or Cloudflare challenges."""
        captcha_indicators = [
            'iframe[src*="recaptcha"]', 'iframe[src*="hcaptcha"]',
            '.g-recaptcha', '.h-captcha', '#cf-challenge-running'
        ]
        for sel in captcha_indicators:
            try:
                el = await page.query_selector(sel)
                if el:
                    return True
            except Exception:
                continue
        return False

    async def _fill_platform_form(
        self,
        page: Page,
        platform: str,
        resume: ResumeData,
        custom: CustomizationResult,
        pdf_path: Optional[str]
    ) -> List[str]:
        """Map and populate standard contact and resume fields with selector fallback."""
        filled: List[str] = []
        name_parts = resume.contact.name.split(" ", 1)
        first_name = name_parts[0] if name_parts else "Candidate"
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        mappings = [
            ("first_name", first_name),
            ("last_name", last_name),
            ("full_name", resume.contact.name),
            ("email", resume.contact.email),
            ("phone", resume.contact.phone),
            ("linkedin", resume.contact.linkedin),
            ("github", resume.contact.github),
            ("cover_letter_text", custom.cover_letter)
        ]

        for field_key, value in mappings:
            if not value:
                continue
            if await self._try_fill_fallback(page, field_key, value):
                filled.append(field_key)

        if pdf_path and Path(pdf_path).exists():
            if await self._try_upload_file(page, "resume_file", pdf_path):
                filled.append("resume_file")

        return filled

    async def _try_fill_fallback(self, page: Page, field_key: str, value: str) -> bool:
        """Attempt filling an input using the cascade of selector fallbacks."""
        selectors = self.SELECTOR_FALLBACKS.get(field_key, [])
        for selector in selectors:
            try:
                elem = await page.query_selector(selector)
                if elem and await elem.is_visible():
                    await elem.fill(value)
                    return True
            except Exception:
                continue
        return False

    async def _try_upload_file(self, page: Page, field_key: str, file_path: str) -> bool:
        """Attempt uploading file to file input using selector fallback."""
        selectors = self.SELECTOR_FALLBACKS.get(field_key, ['input[type="file"]'])
        for selector in selectors:
            try:
                elem = await page.query_selector(selector)
                if elem:
                    await elem.set_input_files(file_path)
                    return True
            except Exception:
                continue
        return False

    async def _submit_form(self, page: Page) -> bool:
        """Trigger submit button using selector fallback."""
        for selector in self.SELECTOR_FALLBACKS["submit_button"]:
            try:
                btn = await page.query_selector(selector)
                if btn and await btn.is_visible():
                    await btn.click()
                    await asyncio.sleep(3)
                    return True
            except Exception:
                continue
        return False
