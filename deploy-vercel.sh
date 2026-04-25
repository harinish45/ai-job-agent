#!/bin/bash
set -e

echo "🚀 AI Job Agent — Vercel Frontend Deploy"
echo "=========================================="
echo ""
echo "⚠️  IMPORTANT: Vercel can ONLY host the frontend."
echo "   The backend (FastAPI + PostgreSQL + Redis + Celery) needs a real server."
echo ""

# Check if we're in the right directory
if [ ! -d "frontend" ]; then
    echo "❌ Error: Run this script from the ai-job-agent project root"
    exit 1
fi

# Check for Vercel CLI
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# Check if backend URL is set
if [ -z "$BACKEND_URL" ]; then
    echo ""
    echo "🔗 Enter your deployed backend API URL:"
    echo "   (e.g., https://ai-job-agent-api.onrender.com)"
    read -p "> " BACKEND_URL
    echo ""
fi

# Create env file for frontend
cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=$BACKEND_URL
EOF

echo "✅ Created frontend/.env.local with BACKEND_URL=$BACKEND_URL"
echo ""

# Deploy to Vercel
cd frontend
echo "🚀 Deploying to Vercel..."
vercel --prod

echo ""
echo "✅ Frontend deployed!"
echo ""
echo "📋 Next steps:"
echo "   1. Make sure your backend CORS allows: $(vercel ls | grep -o 'https://[^ ]*' | head -1)"
echo "   2. Add that domain to your backend's CORS_ORIGINS env var"
echo "   3. Test the full flow: Register → Upload Resume → Search Jobs"
