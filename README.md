# AI Job Agent

An autonomous, AI-powered job search and application system. Upload your resume once, and the agent continuously finds matching jobs, analyzes fit scores, generates tailored cover letters, and can auto-apply on your behalf.

## Architecture

```
ai-job-agent/
├── backend/                 # FastAPI + Celery + PostgreSQL
│   ├── app/
│   │   ├── main.py         # FastAPI app & API routes
│   │   ├── config.py       # Environment configuration
│   │   ├── core/
│   │   │   ├── celery_app.py   # Celery + Redis task queue
│   │   │   └── security.py     # JWT auth, encryption
│   │   ├── models/
│   │   │   ├── database.py     # SQLAlchemy engine
│   │   │   └── models.py       # 10 production-grade ORM models
│   │   └── services/
│   │       ├── resume_parser.py    # OCR + NLP resume parsing
│   │       ├── job_matcher.py      # Multi-dimensional scoring
│   │       ├── job_search.py       # Multi-source aggregator
│   │       └── auto_apply.py       # Playwright form automation
│   ├── alembic/            # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/               # Next.js 14 + Tailwind + React Query
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx        # Dashboard
│   │   └── login/page.tsx
│   ├── components/
│   │   ├── Dashboard.tsx
│   │   ├── StatsPanel.tsx
│   │   ├── ResumeUploader.tsx
│   │   ├── JobList.tsx
│   │   ├── ApplicationTracker.tsx
│   │   └── ProfileSettings.tsx
│   ├── lib/api.ts
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml      # Full stack orchestration
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, Tailwind CSS, TanStack Query, Zustand |
| Backend | FastAPI, SQLAlchemy, Pydantic |
| Database | PostgreSQL 15 |
| Queue | Redis + Celery |
| Automation | Playwright (Chromium) |
| AI Layer | OpenAI GPT-4 / GPT-3.5 |
| Resume Parsing | PyPDF2, python-docx, spaCy, scikit-learn |
| Security | JWT, Fernet encryption, bcrypt |

## Features Implemented

### 1. Resume Intelligence
- [x] PDF/DOCX text extraction
- [x] AI-powered structured parsing (OpenAI GPT-4)
- [x] Skills taxonomy extraction
- [x] Experience level detection
- [x] AI role categorization (Prompt Engineer, ML Engineer, AI Ops, etc.)
- [x] Strength/gap/transferable skill analysis
- [x] Resume improvement suggestions with priority levels

### 2. Smart Job Search
- [x] Multi-source aggregation (LinkedIn, Indeed, Wellfound, RemoteOK, WeWorkRemotely)
- [x] AI role detection with 20+ pattern matchers
- [x] Company career page scraping (hidden jobs)
- [x] Deduplication via content hashing
- [x] Scam detection with 8 heuristic patterns
- [x] Daily automated search via Celery Beat

### 3. Intelligent Matching
- [x] 6-dimension scoring (skills, experience, role, location, salary, culture)
- [x] Configurable weights
- [x] Semantic similarity via TF-IDF + cosine similarity
- [x] Missing skills identification
- [x] Transferable skill gap bridging
- [x] Explainable recommendations

### 4. AI Customization
- [x] Tailored resume bullet rewriting
- [x] Generated cover letters (GPT-4)
- [x] Screening question answers
- [x] "Why this company" / "Why this role" generation
- [x] ATS keyword extraction

### 5. Auto Apply Engine
- [x] Playwright browser automation
- [x] Anti-detection measures
- [x] Platform-specific handlers (Greenhouse, Lever, Workday, LinkedIn Easy Apply, Indeed)
- [x] Generic form field detection & mapping
- [x] Resume/CV file upload
- [x] CAPTCHA detection (not bypass — notifies user)
- [x] Rate limiting & human-like delays
- [x] Screenshot logging

### 6. Application Controls
- [x] Match score threshold (default 80%)
- [x] Company approval requirements
- [x] Industry/company exclusions
- [x] Min salary threshold
- [x] Remote/hybrid/onsite filtering
- [x] Experience level filtering
- [x] Daily application limits

### 7. Tracking Dashboard
- [x] Application status pipeline (New → Applied → Screening → Interview → Offer/Rejected/Ghosted)
- [x] Follow-up date tracking
- [x] Interview round logging
- [x] Platform conversion analytics
- [x] Interview rate & offer rate metrics

### 8. Alerts
- [x] Database schema for alerts
- [x] API endpoints for alert management
- [ ] Email/Slack integration (placeholder)

## Database Schema (10 Models)

1. **User** — Authentication & core identity
2. **UserProfile** — Resume data, preferences, auto-apply rules
3. **PlatformCredential** — Encrypted login credentials per job board
4. **JobListing** — Scraped jobs with AI flags & scam detection
5. **JobMatchScore** — Multi-dimensional scoring + AI-generated materials
6. **JobApplication** — Full application lifecycle tracking
7. **JobAlert** — Notification system
8. **ApplicationLog** — Detailed action logs with screenshots
9. **LearningFeedback** — ML feedback loop for targeting improvement

## Quick Start

### Prerequisites
- Docker & Docker Compose
- OpenAI API key
- 32-byte encryption key

### 1. Clone & Configure
```bash
cd ai-job-agent

cp backend/.env.example backend/.env
# Edit backend/.env:
# OPENAI_API_KEY=sk-...
# ENCRYPTION_KEY=your-32-byte-key-here!!
# SECRET_KEY=your-jwt-secret
```

### 2. Launch
```bash
docker-compose up --build
```

Services:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### 3. First Run
1. Register at http://localhost:3000/login
2. Upload your resume (PDF/DOCX)
3. Configure preferences in Settings
4. Trigger job search or wait for daily auto-run
5. Review matches and save/apply

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Create account |
| POST | /api/auth/login | Get JWT token |
| POST | /api/resume/upload | Upload & parse resume |
| GET | /api/resume/analysis | Get AI analysis |
| GET | /api/profile | Get user profile |
| PUT | /api/profile | Update preferences |
| GET | /api/jobs | List jobs with filters |
| POST | /api/jobs/{id}/match | Calculate match score |
| POST | /api/jobs/{id}/apply | Apply to job |
| GET | /api/applications | List applications |
| PUT | /api/applications/{id}/status | Update status |
| GET | /api/dashboard/stats | Analytics |
| POST | /api/search/trigger | Manual search trigger |

## Celery Tasks

| Task | Schedule | Description |
|------|----------|-------------|
| daily_job_search | Every 24h | Scrape all sources for new jobs |
| process_pending_applications | Every 1h | Auto-apply to queued applications |
| parse_resume_task | On-demand | Async resume parsing |

## Production Considerations

### Security
- All credentials encrypted with Fernet (AES-128)
- JWT tokens for API auth
- Rate limiting on applications (configurable)
- No credential storage in logs

### Scalability
- Celery workers horizontally scalable
- PostgreSQL connection pooling ready
- Redis for distributed task queue
- Playwright browser profiles for persistent sessions

### Ethics & Compliance
- Respects robots.txt (implement per source)
- Configurable rate limits (30-120s between applications)
- Human approval mode available
- CAPTCHA detection — never bypasses, notifies user
- Logs every action for audit trail

## Known Limitations & Roadmap

### Current Gaps
- [ ] LinkedIn/Indeed authenticated scraping (requires credential management UI)
- [ ] Email/Slack alert delivery (schema ready, needs integration)
- [ ] Referral opportunity detection
- [ ] Networking message generation
- [ ] ML feedback loop training (schema ready)
- [ ] Browser profile persistence across container restarts
- [ ] Advanced CAPTCHA handling (2captcha/anti-captcha integration stub)

### Phase 2 Roadmap
- [ ] LinkedIn API integration (official)
- [ ] Indeed API integration
- [ ] Greenhouse/Lever native API support
- [ ] Email parser for application status updates
- [ ] Calendar integration for interview scheduling
- [ ] Chrome extension for one-click save
- [ ] Mobile app (React Native)

## License

MIT — Use at your own risk. Respect website Terms of Service.
