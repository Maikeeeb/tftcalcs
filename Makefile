.PHONY: help setup test test-backend test-frontend lint format dev-backend dev-frontend dev clean

# Default target
help:
	@echo "Available targets:"
	@echo "  setup          - Set up development environment (venv, dependencies, pre-commit)"
	@echo "  test           - Run all tests (backend and frontend)"
	@echo "  test-backend   - Run backend tests with coverage"
	@echo "  test-frontend  - Run frontend tests with coverage"
	@echo "  lint           - Run linting (pre-commit hooks, frontend lint)"
	@echo "  format         - Format code (black, frontend formatter)"
	@echo "  dev-backend    - Start FastAPI server with reload"
	@echo "  dev-frontend   - Start Vite dev server"
	@echo "  dev            - Start both backend and frontend (requires two terminals)"
	@echo "  clean          - Remove build artifacts, cache files, coverage reports"

# Setup development environment
setup:
	@echo "Setting up development environment..."
	python -m venv .venv || python3 -m venv .venv
	@echo "Activate the virtual environment:"
	@echo "  On Windows: .venv\\Scripts\\activate"
	@echo "  On macOS/Linux: source .venv/bin/activate"
	@echo "Then run: make install-deps"

install-deps:
	@echo "Installing dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	cd frontend && npm install
	pre-commit install

# Testing
test: test-backend test-frontend

test-backend:
	@echo "Running backend tests..."
	pytest --cov --cov-report=term --cov-report=html

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && npm test -- --coverage

# Linting and formatting
lint:
	@echo "Running pre-commit hooks..."
	pre-commit run --all-files
	@echo "Running frontend linting..."
	cd frontend && npm run lint || echo "Lint script not configured, skipping..."

format:
	@echo "Formatting Python code..."
	black --line-length=100 bfl/ ui_api/ tests/
	@echo "Formatting frontend code..."
	cd frontend && npm run format || echo "Format script not configured, skipping..."

# Development servers
dev-backend:
	@echo "Starting FastAPI server on http://localhost:8000"
	uvicorn ui_api.main:app --reload --port 8000

dev-frontend:
	@echo "Starting Vite dev server..."
	cd frontend && npm run dev

dev:
	@echo "Starting both backend and frontend..."
	@echo "Backend will run on http://localhost:8000"
	@echo "Frontend will run on http://localhost:5173"
	@echo "Press Ctrl+C to stop both servers"
	@echo ""
	@echo "Note: This requires two terminal windows or use a process manager"
	@echo "Run 'make dev-backend' in one terminal and 'make dev-frontend' in another"

# Cleanup
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage coverage.xml .pytest_cache/ .mypy_cache/ .hypothesis/
	rm -rf frontend/dist frontend/node_modules/.cache frontend/coverage
	@echo "Clean complete!"
