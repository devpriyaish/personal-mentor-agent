.PHONY: help setup install run test clean docker-up docker-down lint format

# Default target
help:
	@echo "Personal Mentor Agent - Available Commands"
	@echo "=========================================="
	@echo "setup          - Run complete setup process"
	@echo "install        - Install dependencies"
	@echo "run            - Run the application"
	@echo "test           - Run tests"
	@echo "docker-up      - Start services with Docker Compose"
	@echo "docker-down    - Stop Docker services"
	@echo "docker-build   - Build Docker image"
	@echo "clean          - Clean temporary files"
	@echo "lint           - Run code linting"
	@echo "format         - Format code"
	@echo "backup         - Backup database"
	@echo "logs           - View application logs"

# Setup
setup:
	@echo "Running setup..."
	python setup.py

# Install dependencies
install:
	pip install -r requirements.txt

# Install development dependencies
install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-cov black flake8 mypy

# Run the application
run:
	streamlit run app.py

# Run with specific port
run-port:
	streamlit run app.py --server.port=8502

# Run tests
test:
	python -m pytest test_mentor.py -v

# Run tests with coverage
test-cov:
	python -m pytest test_mentor.py -v --cov=. --cov-report=html

# Docker commands
docker-up:
	docker-compose up -d
	@echo "Services started! Access the app at http://localhost:8501"

docker-down:
	docker-compose down

docker-build:
	docker-compose build

docker-logs:
	docker-compose logs -f

# Start only Qdrant
qdrant-start:
	docker run -d --name mentor_qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant

qdrant-stop:
	docker stop mentor_qdrant
	docker rm mentor_qdrant

# Code quality
lint:
	flake8 *.py --max-line-length=100 --exclude=venv

format:
	black *.py --line-length=100

type-check:
	mypy *.py --ignore-missing-imports

# Database management
backup:
	@mkdir -p backups
	@cp mentor_data.db backups/mentor_data_$(shell date +%Y%m%d_%H%M%S).db
	@echo "Database backed up to backups/"

restore:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make restore FILE=backups/mentor_data_YYYYMMDD_HHMMSS.db"; \
	else \
		cp $(FILE) mentor_data.db; \
		echo "Database restored from $(FILE)"; \
	fi

# Clean temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

clean-all: clean
	rm -rf venv
	rm -rf data/*
	rm -f mentor_data.db

# View logs
logs:
	@if [ -d "logs" ]; then \
		tail -f logs/mentor_$(shell date +%Y%m%d).log; \
	else \
		echo "No logs directory found"; \
	fi

logs-errors:
	@if [ -d "logs" ]; then \
		tail -f logs/mentor_errors_$(shell date +%Y%m%d).log; \
	else \
		echo "No logs directory found"; \
	fi

# Development
dev-setup: install-dev
	@echo "Development environment ready!"

dev-run:
	STREAMLIT_SERVER_HEADLESS=false streamlit run app.py --server.runOnSave=true

# Production
prod-run:
	streamlit run app.py --server.address=0.0.0.0 --server.port=8501 --server.headless=true

# Health check
health:
	@curl -f http://localhost:8501/_stcore/health || echo "Application not running"

# Initialize database
init-db:
	python -c "from database import DatabaseManager; from config import Config; db = DatabaseManager(Config()); db.initialize_all(); print('Database initialized')"

# Create admin user (for testing)
create-test-user:
	python -c "from database import DatabaseManager; from models import User; from config import Config; from datetime import datetime; db = DatabaseManager(Config()); db.initialize_all(); user = User('test_user', 'Test User', 'test@example.com', datetime.now()); db.create_user(user); print('Test user created')"