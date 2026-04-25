#!/bin/bash
set -e

echo "🚀 AI Job Agent — Full Deployment Script"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git not found. Install Git first.${NC}"
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker not found. You'll need it for local development.${NC}"
fi

echo -e "${GREEN}✅ Prerequisites OK${NC}"
echo ""

# Git setup
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit"
fi

# Check for remote
if ! git remote get-url origin &> /dev/null; then
    echo ""
    echo "🔗 Set up GitHub repository:"
    echo "   1. Create a new repo on GitHub (don't initialize with README)"
    echo "   2. Paste the repo URL below"
    read -p "GitHub repo URL: " REPO_URL
    git remote add origin $REPO_URL
    git branch -M main
    git push -u origin main
    echo -e "${GREEN}✅ Pushed to GitHub${NC}"
else
    echo "🔄 Pushing to existing remote..."
    git add .
    git commit -m "Update: $(date)" || true
    git push
fi

echo ""
echo "📖 Next Steps:"
echo "=============="
echo ""
echo "1. BACKEND — Choose ONE platform:"
echo ""
echo "   A) Render (Easiest):"
echo "      → Go to https://render.com"
echo "      → New → Blueprint → Connect your GitHub repo"
echo "      → Add env vars: OPENAI_API_KEY, ENCRYPTION_KEY, SECRET_KEY"
echo ""
echo "   B) Railway (Simple UI):"
echo "      → Go to https://railway.app"
echo "      → New Project → Deploy from GitHub"
echo "      → Add Postgres + Redis from the UI"
echo "      → Set env vars in the Variables tab"
echo ""
echo "   C) Fly.io (Best Performance):"
echo "      → Install: curl -L https://fly.io/install.sh | sh"
echo "      → Run: fly launch --dockerfile backend/Dockerfile"
echo "      → Run: fly secrets set OPENAI_API_KEY=sk-..."
echo ""
echo "2. FRONTEND — Vercel:"
echo "      → Go to https://vercel.com"
echo "      → Add New Project → Import your GitHub repo"
echo "      → Set Root Directory to: frontend"
echo "      → Add env var: NEXT_PUBLIC_API_URL=<your-backend-url>"
echo ""
echo "3. CONNECT:"
echo "      → Add your Vercel domain to backend CORS_ORIGINS env var"
echo "      → Test: Register → Upload Resume → Search Jobs"
echo ""
echo -e "${GREEN}🎉 Done! Check DEPLOY.md for detailed instructions.${NC}"
