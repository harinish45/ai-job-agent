# Deployment Guide

## The Hard Truth

**Vercel can only host the Next.js frontend.** The backend requires:
- A persistent process (FastAPI server)
- A database (PostgreSQL)
- A message queue (Redis)
- Long-running workers (Celery)
- A real browser (Playwright)

Vercel is serverless — it kills processes after 10 seconds. You need a real server for the backend.

---

## Recommended Stack: Vercel + Render

| Component | Platform | Cost | Why |
|-----------|----------|------|-----|
| **Frontend** | Vercel | **Free** | Best Next.js hosting |
| **API** | Render | **Free** (sleeps after 15min) | Simplest FastAPI deploy |
| **Database** | Render Postgres | **Free** (1GB) | Managed, backups |
| **Redis** | Render Redis | **Free** (25MB) | Managed |
| **Workers** | Render Workers | **$7/mo each** | Celery job processing |

**Minimum viable cost: $0** (skip workers, trigger searches manually)  
**Full auto-apply cost: ~$14/mo** (2 workers)  
**Production cost: ~$25-50/mo**

---

## Step 1: Deploy Backend to Render

### 1.1 Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOURNAME/ai-job-agent.git
git push -u origin main
```

### 1.2 Create Render Account

1. Go to [render.com](https://render.com) → Sign up with GitHub
2. Click "New" → "Blueprint" → Connect your GitHub repo
3. Render auto-detects `render.yaml` and creates all services

### 1.3 Set Environment Variables

In Render Dashboard → each service → Environment:

**Web Service + Workers:**
```
OPENAI_API_KEY=sk-your-key-here
ENCRYPTION_KEY=your-32-byte-key-here!!
SECRET_KEY=your-jwt-secret-key-here
```

Generate keys:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 1.4 Get Your API URL

After deploy, Render gives you a URL like:
```
https://ai-job-agent-api.onrender.com
```

**Save this URL.** You'll need it for the frontend.

---

## Step 2: Deploy Frontend to Vercel

### 2.1 Install Vercel CLI

```bash
npm install -g vercel
```

### 2.2 Deploy

```bash
# From project root
cd frontend

# Set backend URL
echo "NEXT_PUBLIC_API_URL=https://ai-job-agent-api.onrender.com" > .env.local

# Deploy
vercel --prod
```

Or use the web UI:
1. Go to [vercel.com](https://vercel.com) → "Add New Project"
2. Import your GitHub repo
3. Set **Root Directory** to `frontend/`
4. Add Environment Variable: `NEXT_PUBLIC_API_URL=https://ai-job-agent-api.onrender.com`
5. Deploy

### 2.3 Update Backend CORS

In Render Dashboard → Web Service → Environment:

Add your Vercel domain to `CORS_ORIGINS`:
```
CORS_ORIGINS=https://your-app.vercel.app,https://your-app-git-main-yourname.vercel.app
```

Redeploy the web service.

---

## Alternative Backends

### Railway (Even Easier)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy from project root
railway init
railway add --database postgres
railway add --database redis
railway up

# Set secrets
railway variables set OPENAI_API_KEY=sk-...
railway variables set ENCRYPTION_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
railway variables set SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### Fly.io (Best Performance)

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Launch
fly launch --dockerfile backend/Dockerfile
fly postgres create --name jobagent-db
fly redis create --name jobagent-redis
fly secrets set OPENAI_API_KEY=sk-...
fly deploy
```

### Self-Hosted (Cheapest Long-Term)

**Hetzner Cloud** (€4.51/mo for 2GB VPS):
```bash
# On Ubuntu 22.04 server
git clone <repo>
cd ai-job-agent
cp backend/.env.example backend/.env
# Edit .env with your keys
docker-compose up -d
```

---

## One-Click Deploy Buttons

### Render
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOURNAME/ai-job-agent)

*(Replace YOURNAME with your GitHub username after pushing)*

### Railway
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/YOUR_TEMPLATE_ID)

### Vercel
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/YOURNAME/ai-job-agent&root-directory=frontend)

---

## Troubleshooting

### CORS Errors
```
Access to fetch at '...' from origin '...' has been blocked by CORS
```
**Fix:** Add your Vercel domain to backend `CORS_ORIGINS` env var.

### 502 Bad Gateway
**Fix:** Backend is sleeping (Render free tier). Visit the API URL once to wake it up.

### Database Connection Errors
**Fix:** Check `DATABASE_URL` format. Should be:
```
postgresql://user:pass@host:5432/dbname
```

### Redis Connection Errors
**Fix:** Check `REDIS_URL` format. Should be:
```
redis://host:6379/0
```

### OpenAI Errors
**Fix:** Check `OPENAI_API_KEY` is set and has billing enabled.

---

## Architecture Diagram

```
┌─────────────────┐         ┌─────────────────────────────────────┐
│   Vercel        │         │   Render / Railway / Fly / VPS      │
│                 │         │                                     │
│  ┌───────────┐  │  HTTPS  │  ┌─────────┐   ┌──────────────┐   │
│  │ Next.js   │──┼────────→│  │ FastAPI │──→│ PostgreSQL   │   │
│  │ Frontend  │  │         │  │   API   │   │   Database   │   │
│  └───────────┘  │         │  └────┬────┘   └──────────────┘   │
│                 │         │       │                           │
└─────────────────┘         │  ┌────┴────┐   ┌──────────────┐   │
                            │  │ Celery  │──→│    Redis     │   │
                            │  │ Workers │   │    Queue     │   │
                            │  └─────────┘   └──────────────┘   │
                            │                                     │
                            │  ┌─────────┐   ┌──────────────┐   │
                            │  │ Celery  │   │  Playwright  │   │
                            │  │  Beat   │   │   Browser    │   │
                            │  └─────────┘   └──────────────┘   │
                            └─────────────────────────────────────┘
```
