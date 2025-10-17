.PHONY: help install dev-install lint format type-check test test-cov clean pre-commit setup

# Default target
.DEFAULT_GOAL := help

# Colors
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Atoms MCP - Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ============================================================================
# Installation
# ============================================================================

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	uv sync --frozen

dev-install: ## Install development dependencies
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	uv sync --frozen --group dev
	@echo "$(GREEN)✓ Development dependencies installed$(NC)"

setup: dev-install pre-commit-install ## Complete development setup
	@echo "$(GREEN)✓ Development environment ready!$(NC)"

# ============================================================================
# Code Quality
# ============================================================================

lint: ## Run linting (ruff)
	@echo "$(BLUE)Running ruff linter...$(NC)"
	ruff check . --fix
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: ## Format code (ruff + black)
	@echo "$(BLUE)Formatting code...$(NC)"
	ruff format .
	black .
	isort .
	@echo "$(GREEN)✓ Formatting complete$(NC)"

type-check: ## Run type checking (zuban)
	@echo "$(BLUE)Running type checker...$(NC)"
	uv run zuban mypy .
	@echo "$(GREEN)✓ Type checking complete$(NC)"

check: lint type-check ## Run all checks (lint + type-check)
	@echo "$(GREEN)✓ All checks passed$(NC)"

# ============================================================================
# Testing
# ============================================================================

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest

test-cov: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest --cov=. --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/$(NC)"

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest -m unit

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest -m integration

test-e2e: ## Run end-to-end tests only
	@echo "$(BLUE)Running end-to-end tests...$(NC)"
	pytest -m e2e

test-fast: ## Run tests in parallel (fast)
	@echo "$(BLUE)Running tests in parallel...$(NC)"
	pytest -n auto

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	pytest-watch

# ============================================================================
# Performance & Benchmarking
# ============================================================================

benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running performance benchmarks...$(NC)"
	pytest tests/performance/ --benchmark-only --benchmark-autosave

benchmark-compare: ## Compare benchmark results
	@echo "$(BLUE)Comparing benchmark results...$(NC)"
	pytest-benchmark compare

profile-memory: ## Profile memory usage
	@echo "$(BLUE)Profiling memory usage...$(NC)"
	python -m memory_profiler scripts/profile_memory.py

load-test: ## Run load tests
	@echo "$(BLUE)Running load tests...$(NC)"
	locust -f tests/load/locustfile.py --headless -u 100 -r 10 -t 60s

load-test-ui: ## Run load tests with UI
	@echo "$(BLUE)Starting Locust UI...$(NC)"
	@echo "$(YELLOW)Open http://localhost:8089 in your browser$(NC)"
	locust -f tests/load/locustfile.py

# ============================================================================
# Code Quality Analysis
# ============================================================================

complexity: ## Analyze code complexity
	@echo "$(BLUE)Analyzing code complexity...$(NC)"
	radon cc . -a -s
	radon mi . -s

complexity-check: ## Check complexity thresholds
	@echo "$(BLUE)Checking complexity thresholds...$(NC)"
	xenon --max-absolute B --max-modules A --max-average A .

dead-code: ## Detect dead code
	@echo "$(BLUE)Detecting dead code...$(NC)"
	vulture . --min-confidence 80

duplication: ## Check for code duplication
	@echo "$(BLUE)Checking for code duplication...$(NC)"
	pylint --disable=all --enable=duplicate-code .

doc-coverage: ## Check documentation coverage
	@echo "$(BLUE)Checking documentation coverage...$(NC)"
	interrogate -v --fail-under 80 .

quality-report: ## Generate comprehensive quality report
	@echo "$(BLUE)Generating quality report...$(NC)"
	prospector --profile prospector.yaml

# ============================================================================
# Dependency Analysis
# ============================================================================

deps-tree: ## Show dependency tree
	@echo "$(BLUE)Dependency tree:$(NC)"
	pipdeptree

deps-graph: ## Generate dependency graph
	@echo "$(BLUE)Generating dependency graph...$(NC)"
	pydeps . --max-bacon=2 --cluster --rankdir=TB -o dependency_graph.svg
	@echo "$(GREEN)✓ Graph saved to dependency_graph.svg$(NC)"

deps-audit: ## Audit dependencies for vulnerabilities
	@echo "$(BLUE)Auditing dependencies...$(NC)"
	pip-audit

deps-licenses: ## Show dependency licenses
	@echo "$(BLUE)Dependency licenses:$(NC)"
	pip-licenses --format=markdown

# ============================================================================
# Pre-commit
# ============================================================================

pre-commit-install: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

pre-commit-run: ## Run pre-commit on all files
	@echo "$(BLUE)Running pre-commit on all files...$(NC)"
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks
	@echo "$(BLUE)Updating pre-commit hooks...$(NC)"
	pre-commit autoupdate

# ============================================================================
# Atoms CLI
# ============================================================================

start: ## Start local server
	./atoms start

deploy-preview: ## Deploy to preview
	./atoms deploy --preview

deploy-prod: ## Deploy to production
	./atoms deploy --production

vendor: ## Vendor pheno-sdk packages
	./atoms vendor setup --clean

schema-check: ## Check schema drift
	./atoms schema check

schema-sync: ## Sync schemas from database
	./atoms schema sync

deployment-check: ## Check deployment readiness
	./atoms check

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Clean build artifacts
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .zuban_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-all: clean ## Clean everything including venv
	@echo "$(BLUE)Cleaning everything...$(NC)"
	rm -rf .venv/
	@echo "$(GREEN)✓ Deep cleanup complete$(NC)"

# ============================================================================
# Documentation
# ============================================================================

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	@echo "$(YELLOW)Not implemented yet$(NC)"

# ============================================================================
# CI/CD
# ============================================================================

ci: lint type-check test ## Run CI checks locally
	@echo "$(GREEN)✓ All CI checks passed$(NC)"

ci-fast: ## Run fast CI checks (no type-check)
	@echo "$(BLUE)Running fast CI checks...$(NC)"
	ruff check .
	pytest -n auto --maxfail=1
	@echo "$(GREEN)✓ Fast CI checks passed$(NC)"

# ============================================================================
# Utilities
# ============================================================================

requirements-update: ## Update requirements files
	@echo "$(BLUE)Updating requirements...$(NC)"
	pip-compile requirements.in -o requirements.txt
	@echo "$(GREEN)✓ Requirements updated$(NC)"

show-outdated: ## Show outdated packages
	@echo "$(BLUE)Checking for outdated packages...$(NC)"
	pip list --outdated

version: ## Show version information
	@echo "$(BLUE)Version Information:$(NC)"
	@python --version
	@pip --version
	@echo ""
	@echo "$(BLUE)Installed Tools:$(NC)"
	@ruff --version || echo "ruff: not installed"
	@black --version || echo "black: not installed"
	@zuban --version || echo "zuban: not installed"
	@pytest --version || echo "pytest: not installed"
