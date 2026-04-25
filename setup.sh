#!/bin/bash
set -e

echo "🚀 AI Job Agent Setup"
echo "====================="

# Check prerequisites
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Create .env if not exists
if [ ! -f backend/.env ]; then
    echo "📝 Creating backend/.env from example..."
    cp backend/.env.example backend/.env
    echo "⚠️  Please edit backend/.env and add your:"
    echo "   - OPENAI_API_KEY"
    echo "   - ENCRYPTION_KEY (32 bytes)"
    echo "   - SECRET_KEY"
    echo ""
    read -p "Press Enter after editing .env to continue..."
fi

# Build and start
echo "🏗️  Building services..."
docker-compose up --build -d

# Wait for DB
echo "⏳ Waiting for database..."
sleep 5

# Run migrations
echo "🗄️  Running database migrations..."
docker-compose exec -T backend alembic upgrade head

echo ""
echo "✅ Setup complete!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔌 API:      http://localhost:8000"
echo "📚 Docs:     http://localhost:8000/docs"
echo ""
echo "📝 Next steps:"
echo "   1. Register at http://localhost:3000/login"
echo "   2. Upload your resume"
echo "   3. Configure preferences in Settings"
echo "   4. Trigger job search or wait for daily auto-run"
