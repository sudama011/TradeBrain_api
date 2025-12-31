# --- Variables ---
VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
UVICORN = $(VENV)/bin/uvicorn
BIN = $(VENV)/bin

# Colors for terminal output
BLUE = \033[1;34m
GREEN = \033[1;32m
RESET = \033[0m

# Default target
.DEFAULT_GOAL := help

# Phony targets to avoid conflicts with file names
.PHONY: install run scan clean docker-up db-up lint lint-fix format help

# --- Help Message ---
help:
	@echo "$(BLUE)Makefile commands:$(RESET)"
	@echo "  $(GREEN)install$(RESET)       🛠️  Setup: Creates .venv and installs dependencies"
	@echo "  $(GREEN)run$(RESET)           🚀  Run API: Starts the FastAPI server"
	@echo "  $(GREEN)scan$(RESET)          🕵️  Run Scanner: Starts the background worker"
	@echo "  $(GREEN)clean$(RESET)         🧹  Clean: Removes cache files"
	@echo "  $(GREEN)docker-up$(RESET)     🐳  Docker: Builds and starts all services in Docker"
	@echo "  $(GREEN)db-up$(RESET)         🐘  DB: Starts PostgreSQL in Docker"
	@echo "  $(GREEN)lint$(RESET)          🔍  Lint: Runs code quality checks"
	@echo "  $(GREEN)lint-fix$(RESET)      🛠️  Lint: Fixes auto-fixable issues"
	@echo "  $(GREEN)format$(RESET)        🎨  Format: Auto-formats code with Black"

# --- Core Commands ---

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Setup complete. Activate with: source .venv/bin/activate$(RESET)"

run:
	$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# --- Docker ---

docker-up:
	docker-compose up -d --build

db-up:
	docker-compose up -d db

# --- Code Quality ---

lint: ## Run all linting checks
	@echo "$(BLUE)🔍 Running linting checks...$(RESET)"
	# We ignore E501 (line too long) because strict 79 chars is annoying
	$(BIN)/flake8 app --ignore=E501
	$(BIN)/mypy app --ignore-missing-imports
	@echo "$(GREEN)✅ Linting completed$(RESET)"

lint-fix: ## Fix auto-fixable linting issues
	@echo "$(BLUE)🔧 Fixing linting issues...$(RESET)"
	$(BIN)/autopep8 --in-place --recursive --aggressive app
	@echo "$(GREEN)✅ Auto-fixable issues resolved$(RESET)"

format: ## Format code with black and isort
	@echo "$(BLUE)🎨 Formatting code...$(RESET)"
	$(BIN)/black app
	$(BIN)/isort app
	@echo "$(GREEN)✅ Code formatting completed$(RESET)"