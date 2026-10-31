# 📋 TODO & Master Plan — ai-job-agent

> **Project**: AI Job Application Agent — Autonomous Resume Tailoring & Auto-Apply
> **Stack**: Python, Playwright, LLM APIs, Docker, FastAPI, Next.js
> **Status**: 🟢 Core Engine & Auto-Apply Complete (~95%)
> **Last Updated**: 2026-10-31

## 🏗️ Architecture
```
ai-job-agent/
├── Makefile            # Build and development commands
├── DEPLOY.md           # Deployment guide (Fly.io, Railway, Render, Docker)
├── PRD.md              # Product requirements document
├── AGENTS.md           # Agent architecture and execution guidelines
├── docker-compose.yml  # Multi-service container orchestration
├── fly.toml            # Fly.io deployment config
├── railway.toml        # Railway deployment config
├── render.yaml         # Render deployment config
├── setup.sh            # Local automated setup script
├── requirements.txt    # Core Python dependencies
├── .env.example        # Environment variable template
├── src/                # Core autonomous application agent engine
│   ├── models.py       # Data structures & typed dataclasses
│   ├── resume_parser.py# PDF & text resume parser
│   ├── job_analyzer.py # Job analyzer & 0-100% ATS keyword matcher
│   ├── llm_generator.py# Tailored resume & cover letter generator (Gemini/OpenAI)
│   ├── auto_apply.py   # Playwright automation engine with selector fallback
│   └── tracker.py      # SQLite & JSON application tracking database
├── scripts/            # Executable CLI tools
│   └── run_agent.py    # Main CLI entry point
├── tests/              # Automated unit and integration test suite
├── backend/            # FastAPI REST API, Alembic migrations & Celery workers
└── frontend/           # Next.js 14 telemetry & application tracker UI
```

## ✅ Completed

### Phase 1 — Core Engine
- [x] PDF & text resume parser (`src/resume_parser.py`)
- [x] Job description NLP extractor (`src/job_analyzer.py`)
- [x] ATS keyword matcher and 0-100% score calculation (`src/job_analyzer.py`)
- [x] LLM-powered resume tailoring with OpenAI & Gemini compatibility (`src/llm_generator.py`)
- [x] Cover letter generator with mock fallback (`src/llm_generator.py`)

### Phase 2 — Auto-Apply & Tracking
- [x] Playwright browser automation scaffold (`src/auto_apply.py`)
- [x] Multi-platform ATS support: Greenhouse, Lever, Workday, LinkedIn, Indeed
- [x] Form field mapping with selector fallback chains
- [x] CAPTCHA detection and dry-run safety modes
- [x] Application lifecycle tracking store (`src/tracker.py`)
- [x] Status management (Applied, Screening, Interview, Offer, Rejected)
- [x] Command-line interface `scripts/run_agent.py` (parse, analyze, match, tailor, track, batch)

### Deployment & Infrastructure
- [x] Multi-platform deployment configs (Docker, Fly.io, Railway, Render)
- [x] Next.js frontend dashboard
- [x] FastAPI REST backend + Celery task queue
- [x] Root environment template `.env.example`
- [x] Comprehensive test suite in `tests/` (100% passing)

## 🚀 Roadmap

### Phase 3 — Intelligence (Q1 2027)
- [x] Job match scoring (0-100)
- [ ] Company research agent
- [ ] Salary negotiation assistant
- [ ] Interview prep Q&A generator
- [ ] Follow-up email automation

### Phase 4 — Production Polish (Q2 2027)
- [x] Web UI for job queue management
- [x] Background scheduling (Celery beat)
- [ ] Email/Slack webhook notifications
- [x] Analytics dashboard metrics (apply rate, interview rate)

## 🐛 Resolved Issues
- [x] Main agent scripts committed in `src/` and `scripts/`
- [x] Automated unit test suite implemented in `tests/`
- [x] Root `.env.example` and `requirements.txt` added
