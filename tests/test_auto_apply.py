"""
Unit tests for Auto Apply Engine platform detection and fallback mechanisms.
"""

from src.auto_apply import AutoApplyEngine


def test_detect_platform():
    engine = AutoApplyEngine(headless=True)

    assert engine.detect_platform("https://boards.greenhouse.io/company/jobs/123", "") == "greenhouse"
    assert engine.detect_platform("https://jobs.lever.co/company/456", "") == "lever"
    assert engine.detect_platform("https://www.linkedin.com/jobs/view/789", "") == "linkedin_easy_apply"
    assert engine.detect_platform("https://www.indeed.com/viewjob?jk=abc", "") == "indeed"
    assert engine.detect_platform("https://myworkdayjobs.com/company", "") == "workday"
    assert engine.detect_platform("https://example.com/careers/apply", "") == "generic"


def test_selector_fallbacks_present():
    engine = AutoApplyEngine(headless=True)
    assert "first_name" in engine.SELECTOR_FALLBACKS
    assert "email" in engine.SELECTOR_FALLBACKS
    assert "resume_file" in engine.SELECTOR_FALLBACKS
    assert len(engine.SELECTOR_FALLBACKS["email"]) >= 3
