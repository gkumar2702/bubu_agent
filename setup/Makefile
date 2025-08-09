.PHONY: help format lint typecheck test test-cov clean install install-dev all dev check

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  format       - Format code with black and isort"
	@echo "  lint         - Run ruff linter"
	@echo "  typecheck    - Run mypy type checker"
	@echo "  test         - Run tests"
	@echo "  test-cov     - Run tests with coverage"
	@echo "  clean        - Clean up cache files"
	@echo "  all          - Run format, lint, typecheck, and test"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

# Code formatting
format:
	ruff format .
	ruff check --fix .

# Linting
lint:
	ruff check .

# Type checking
typecheck:
	mypy utils/ providers/ --strict

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=utils --cov=providers --cov-report=term-missing --cov-report=html

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

# Run all checks
all: format lint typecheck test

# Development workflow
dev: install-dev format lint typecheck test

# Quick check (no formatting)
check: lint typecheck test
