.PHONY: help install run test lint clean format check

# Default target
help:
	@echo "Bubu Agent - Available commands:"
	@echo "  install  - Install dependencies"
	@echo "  run      - Run the application"
	@echo "  test     - Run tests"
	@echo "  lint     - Run linting and type checking"
	@echo "  format   - Format code with black and isort"
	@echo "  check    - Run format check"
	@echo "  clean    - Clean up generated files"

# Install dependencies
install:
	pip install -e .
	pip install -e ".[dev]"

# Run the application
run:
	uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Run tests
test:
	pytest tests/ -v --tb=short

# Run tests with coverage
test-cov:
	pytest tests/ -v --tb=short --cov=. --cov-report=html --cov-report=term

# Run linting and type checking
lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
	mypy . --ignore-missing-imports

# Format code
format:
	black .
	isort .

# Check if code is formatted
check:
	black . --check
	isort . --check-only

# Clean up generated files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -f bubu_agent.db

# Virtual environment setup
venv:
	@echo "Creating virtual environment..."
	python -m venv venv
	@echo "Virtual environment created. Activate it with:"
	@echo "  source venv/bin/activate  # On macOS/Linux"
	@echo "  venv\\Scripts\\activate     # On Windows"

# Development setup
dev-setup: venv install
	@echo "Setting up development environment..."
	@if [ ! -f .env ]; then cp env.example .env; echo "Created .env from env.example"; fi
	@echo "Please edit .env with your configuration values"
	@echo "Activate virtual environment with: source venv/bin/activate"

# Production setup
prod-setup: install
	@echo "Setting up production environment..."
	@echo "Please ensure you have set up your .env file with production values"

# Activate virtual environment (macOS/Linux)
activate:
	@echo "Activating virtual environment..."
	@echo "Run: source venv/bin/activate"

# Activate virtual environment (Windows)
activate-win:
	@echo "Activating virtual environment..."
	@echo "Run: venv\\Scripts\\activate"

# Deactivate virtual environment
deactivate:
	@echo "Deactivate virtual environment with: deactivate"

# Clean virtual environment
clean-venv:
	@echo "Removing virtual environment..."
	rm -rf venv/
	@echo "Virtual environment removed"

# Docker build (if using Docker)
docker-build:
	docker build -t bubu-agent .

# Docker run (if using Docker)
docker-run:
	docker run -p 8000:8000 --env-file .env bubu-agent
