# 📋 TODO & Master Plan — ai-job-agent

> **Project**: AI Job Application Agent — Autonomous Resume Tailoring & Auto-Apply
> **Stack**: Python, Playwright, LLM APIs, Docker
> **Status**: 🟡 In Progress (~65%)
> **Last Updated**: 2026-10-30

## 🏗️ Architecture
\\\
ai-job-agent/
├── Makefile            # Build commands
├── DEPLOY.md           # Deployment guide
├── PRD.md              # Product requirements
├── docker-compose.yml  # Container orchestration
├── fly.toml            # Fly.io deployment
├── railway.toml        # Railway deployment
├── render.yaml         # Render deployment
├── setup.sh            # Local setup
└── scripts/            # Agent scripts
\\\

## ✅ Completed
- [x] Multi-platform deployment configs (Docker, Fly.io, Railway, Render)
- [x] Makefile for streamlined builds
- [x] DEPLOY.md documentation
- [x] PRD + AGENTS.md
- [x] LICENSE

## 🔧 In Progress
- [ ] Resume tailoring LLM pipeline
- [ ] ATS keyword extraction
- [ ] Browser automation (Playwright)

## 🚀 Roadmap

### Phase 1 — Core Engine (Nov 2026)
- [ ] PDF resume parser
- [ ] Job description NLP extractor (skills, requirements)
- [ ] ATS keyword matcher
- [ ] LLM-powered resume tailoring (Gemini/GPT-4)
- [ ] Cover letter generator

### Phase 2 — Auto-Apply (Nov–Dec 2026)
- [ ] LinkedIn Easy Apply automation
- [ ] Indeed one-click apply
- [ ] Workday form auto-fill
- [ ] Greenhouse / Lever application
- [ ] Job tracking dashboard (Applied/Interview/Rejected)

### Phase 3 — Intelligence (Jan 2027)
- [ ] Job match scoring (0-100)
- [ ] Company research agent
- [ ] Salary negotiation assistant
- [ ] Interview prep Q&A generator
- [ ] Follow-up email automation

### Phase 4 — Production (Feb 2027)
- [ ] Web UI for job queue management
- [ ] Scheduling (run daily at 9 AM)
- [ ] Email/Slack notifications
- [ ] Analytics dashboard (apply rate, interview rate)

## 🐛 Known Issues
- [ ] Main agent scripts not committed yet (only deployment configs)
- [ ] No test suite
- [ ] Missing .env.example for API keys