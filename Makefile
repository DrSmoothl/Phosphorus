# Makefile for Phosphorus project
.PHONY: help install lint format test security clean dev-setup

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	uv sync --extra dev

dev-setup: ## Set up development environment
	uv sync --extra dev
	uv run pre-commit install
	@echo "✅ Development environment set up successfully!"

format: ## Format code with ruff
	@echo "🎨 Formatting code..."
	uv run ruff format src/ tests/ examples/

format-check: ## Check code formatting
	@echo "🎨 Checking code formatting..."
	uv run ruff format --check src/ tests/ examples/

lint: ## Run all linting tools
	@echo "🔍 Running Ruff..."
	uv run ruff check src/ tests/ examples/
	@echo "🐍 Running Pylint..."
	uv run pylint src/ --rcfile=pylint.toml || true
	@echo "🔎 Running MyPy..."
	uv run mypy src/ || true

lint-fix: ## Run linting with auto-fix
	@echo "🔧 Running Ruff with auto-fix..."
	uv run ruff check --fix src/ tests/ examples/

security: ## Run security checks
	@echo "🔒 Running Bandit security check..."
	uv run bandit -r src/ -c pyproject.toml || true
	@echo "🛡️ Running Safety vulnerability check..."
	uv run safety check || true

test: ## Run tests
	@echo "🧪 Running tests..."
	uv run pytest tests/ -v

test-cov: ## Run tests with coverage
	@echo "🧪 Running tests with coverage..."
	uv run pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

ci-check: format-check lint security test ## Run all CI checks locally

clean: ## Clean up generated files
	@echo "🧹 Cleaning up..."
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run: ## Run the development server
	@echo "🚀 Starting Phosphorus server..."
	uv run python -m src.main

run-dev: ## Run the development server with auto-reload
	@echo "🚀 Starting Phosphorus development server..."
	uv run python run_dev.py

docker-build: ## Build Docker image
	docker build -t phosphorus:latest .

docker-run: ## Run Docker container
	docker run -p 8000:8000 phosphorus:latest

all: clean install format lint security test ## Run complete development workflow
