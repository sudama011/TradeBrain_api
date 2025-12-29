# --- Variables ---
VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
UVICORN = $(VENV)/bin/uvicorn

# --- Commands ---

# 🛠️ Setup: Creates .venv and installs dependencies
install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "✅ Setup complete. Activate with: source .venv/bin/activate"

# 🚀 Run API: Starts the FastAPI server in development mode
run:
	$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

# 🕵️ Run Scanner: Starts the background worker (Scanner)
# Note: We use -m to run it as a module so imports work correctly
scan:
	$(PYTHON) -m scanner.main_scanner

# 🧹 Clean: Removes cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# 🐳 Docker: (Future use)
docker-up:
	docker-compose up -d --build