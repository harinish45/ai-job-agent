# 📋 Product Requirements Document (PRD)
## Project: AI Job Agent (Autonomous Job Discovery & Auto-Apply Pipeline)
**Version:** 1.2.0-PROD  
**Owner:** Harinish S V ([@harinish45](https://github.com/harinish45))

---

## 1. Problem Statement
Job hunting is fragmented, repetitive, and time-consuming. Candidates spend hundreds of hours manually tailoring resumes, filling repetitive application forms, and tracking application outcomes across dozens of ATS portals (Greenhouse, Lever, Workday).

## 2. Product Objectives
1. Automatically aggregate job openings across 5+ platforms with scam heuristics.
2. Provide multi-dimensional fit scoring and dynamic resume tailoring.
3. Automate application form submissions via Playwright with anti-detection and human-in-the-loop safeguards.
4. Provide a unified real-time telemetry and conversion rate dashboard.

## 3. Core Modules
* **Resume Parser Engine:** Extract skills, roles, and experience levels with structured LLM prompts.
* **Aggregator & Scraper:** Continuous job scraping with deduplication hashes.
* **Auto-Apply Worker:** Playwright browser automation with field mapping and screenshot logging.
* **Notification Dispatcher:** Real-time application updates and interview request alerts.
