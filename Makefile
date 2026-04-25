.PHONY: up down build logs test migrate shell

# Start all services
up:
	docker-compose up -d

# Build and start
build:
	docker-compose up --build -d

# Stop all services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Run backend tests
test:
	docker-compose exec backend pytest -v

# Run database migrations
migrate:
	docker-compose exec backend alembic upgrade head

# Create new migration
migration:
	docker-compose exec backend alembic revision --autogenerate -m "$(msg)"

# Shell into backend
shell:
	docker-compose exec backend /bin/sh

# Shell into database
psql:
	docker-compose exec db psql -U jobagent -d jobagent

# Clean everything
clean:
	docker-compose down -v
	docker system prune -f

# Setup from scratch
setup:
	cp backend/.env.example backend/.env
	docker-compose up --build -d
	@echo "Waiting for services to start..."
	@sleep 10
	docker-compose exec backend alembic upgrade head
	@echo "Setup complete! Frontend: http://localhost:3000 | API: http://localhost:8000"
