<div align="center">

# 💼 AI Job Agent

**Autonomous AI-Powered Job Application System**

[![CI](https://github.com/harinish45/ai-job-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/harinish45/ai-job-agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](docker-compose.yml)

> *Upload your resume once — the agent finds jobs, tailors your application, and auto-applies 24/7*

[📋 TODO](TODO.md) · [🚀 DEPLOY](DEPLOY.md) · [📄 PRD](PRD.md)

</div>

---

## 🏗️ Architecture

```mermaid
graph TB
    subgraph Input["📥 Input"]
        Resume["📄 Resume\n(PDF)"]
        Prefs["⚙️ Job Preferences\n(role, location, salary)"]
    end

    subgraph Engine["🤖 AI Agent Engine"]
        Parser["🔤 Resume Parser\n(PDF → structured)"]
        Matcher["🎯 Job Matcher\n(ATS keyword scoring)"]
        Tailor["✏️ Resume Tailor\n(LLM rewrite)"]
        CoverLetter["📝 Cover Letter\nGenerator"]
        ApplyBot["🤖 Apply Bot\n(Playwright)"]
    end

    subgraph JobSources["🌐 Job Boards"]
        LinkedIn["💼 LinkedIn\nEasy Apply"]
        Indeed["🔍 Indeed\nOne-Click"]
        Workday["🏢 Workday\nATS Forms"]
    end

    subgraph Tracking["📊 Job Tracker"]
        Dashboard["📈 Dashboard\n(Applied/Interview/Rejected)"]
        Notifications["🔔 Notifications\n(Email/Slack)"]
    end

    Resume --> Parser
    Prefs --> Matcher
    Parser --> Matcher
    Matcher --> Tailor
    Tailor --> CoverLetter
    CoverLetter --> ApplyBot
    ApplyBot --> LinkedIn
    ApplyBot --> Indeed
    ApplyBot --> Workday
    ApplyBot --> Tracking
```

---

## 🔄 Agent Loop

```mermaid
sequenceDiagram
    participant A as Agent
    participant JB as Job Board
    participant LLM as Gemini/GPT
    participant U as User

    loop Every 6 hours
        A->>JB: Search jobs (role + location)
        JB-->>A: Job listings
        A->>A: Filter by ATS score > 70%
        A->>LLM: Tailor resume for top matches
        LLM-->>A: Tailored resume + cover letter
        A->>JB: Auto-apply (Playwright)
        JB-->>A: Confirmation
        A->>U: 📧 Email summary (X applications sent)
    end
```

---

## 🚀 Quick Start

```bash
git clone https://github.com/harinish45/ai-job-agent.git
cd ai-job-agent
./setup.sh

# Or Docker
docker compose up --build
```

---

## 🌐 Deployment Options

| Platform | Config | Command |
|----------|--------|---------|
| Docker | `docker-compose.yml` | `docker compose up` |
| Fly.io | `fly.toml` | `fly deploy` |
| Railway | `railway.toml` | `railway up` |
| Render | `render.yaml` | Auto-deploy |
| Vercel | — | `./deploy-vercel.sh` |

---

<div align="center">
⚠️ Use responsibly — respect platform ToS · <a href="LICENSE">MIT License</a>
</div>