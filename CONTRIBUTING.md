# Contributing to tftcalcs

Thank you for your interest in contributing! This document provides guidelines for setting up the development environment, running tests, and submitting pull requests.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Node.js 16+ and npm (for frontend development)
- Git

### Python Environment Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd tftcalcs
   ```

2. **Set up the development environment:**
   
   **Option A: Using Makefile (Unix/macOS/WSL):**
   ```bash
   make setup
   # Then activate the virtual environment:
   source .venv/bin/activate
   make install-deps
   ```
   
   **Option B: Manual setup:**
   ```bash
   # Create and activate a virtual environment
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   
   # Install production dependencies
   pip install -r requirements.txt
   
   # Install development dependencies
   pip install -r requirements-dev.txt
   
   # Install frontend dependencies
   cd frontend && npm install && cd ..
   ```
   
   **Note:** Windows users without `make` can use the manual setup (Option B) or install `make` via Chocolatey or use WSL.

### Frontend Setup

If you plan to work on the frontend:

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install npm dependencies:**
   ```bash
   npm install
   ```

3. **Return to repository root:**
   ```bash
   cd ..
   ```

### Pre-commit Hooks

Pre-commit hooks automatically run code quality checks before each commit. Install them:

```bash
pre-commit install
```

This will run:
- `black` (code formatter)
- `flake8` (linter)
- `mypy` (type checker)
- Various file checks (trailing whitespace, YAML/JSON validation, etc.)

To run hooks manually on all files:
```bash
pre-commit run --all-files
```

## Using Makefile

The project includes a `Makefile` with convenient shortcuts for common tasks. On Unix/macOS/WSL, you can use:

- `make setup` - Set up development environment
- `make test` - Run all tests (backend and frontend)
- `make test-backend` - Run only backend tests
- `make test-frontend` - Run only frontend tests
- `make lint` - Run linting checks
- `make format` - Format code
- `make dev-backend` - Start FastAPI server
- `make dev-frontend` - Start Vite dev server
- `make clean` - Remove build artifacts

See `make help` for a full list of available targets.

## Testing

### Running Tests

**Using Makefile:**
```bash
make test              # Run all tests
make test-backend      # Backend only
make test-frontend     # Frontend only
```

**Manual commands:**
```bash
pytest                 # Run backend tests
pytest --cov           # With coverage
```

Run tests with coverage reporting:
```bash
pytest --cov
```

View detailed HTML coverage report:
```bash
pytest --cov
# Then open htmlcov/index.html in your browser
```

### Coverage Requirements

The project targets **90% code coverage** for `bfl/` and `ui_api/` packages. Coverage reports are generated in multiple formats:
- Terminal output showing missing lines
- HTML report in `htmlcov/` directory
- XML report in `coverage.xml` (for CI/CD integration)

### Test Markers

Tests are organized with markers for easy filtering:

- `@pytest.mark.unit` - Unit tests for individual functions/modules
- `@pytest.mark.integration` - Integration tests that exercise multiple components
- `@pytest.mark.slow` - Tests that take a long time to run
- `@pytest.mark.api` - Tests that require the FastAPI server
- `@pytest.mark.ui` - Tests that require the React frontend

Run specific test categories:
```bash
pytest -m unit          # Run only unit tests
pytest -m integration   # Run only integration tests
pytest -m "not slow"    # Skip slow tests
```

### Integration Tests

Integration tests are located in `tests/integration/` and cover:
- FastAPI endpoint testing (`test_api_flow.py`)
- End-to-end UI → API → Solver flow (`test_e2e.py`)
- Solver API integration (`test_solver_api.py`)

## Code Style

### Python Code Style

The project uses the following tools for code quality:

- **black**: Code formatter (line length: 100)
- **flake8**: Linter for PEP 8 compliance (max line length: 100, ignores E203, W503)
- **mypy**: Static type checker (with `--ignore-missing-imports`)

All code style checks are enforced via pre-commit hooks. Ensure your code passes these checks before submitting a PR.

### Docstring Style

Use Google/NumPy style docstrings for consistency. Include:
- Brief description
- Parameter descriptions with types
- Return type and description
- Usage examples for complex functions (where helpful)

Example:
```python
def example_function(param1: str, param2: int) -> bool:
    """Brief description of what the function does.

    Parameters
    ----------
    param1 : str
        Description of param1.
    param2 : int
        Description of param2.

    Returns
    -------
    bool
        Description of return value.
    """
```

## Pull Request Guidelines

### Before Submitting

1. **Ensure all tests pass:**
   ```bash
   pytest
   ```

2. **Verify coverage requirements:**
   ```bash
   pytest --cov
   ```
   Ensure coverage remains at or above 90% for `bfl/` and `ui_api/` packages.

3. **Run pre-commit checks:**
   ```bash
   pre-commit run --all-files
   ```

4. **Update documentation:**
   - Add docstrings for new public functions/classes
   - Update README.md if adding new features
   - Update CONTRIBUTING.md if changing development workflow

### Commit Messages

Use clear, descriptive commit messages:
- Use present tense ("Add feature" not "Added feature")
- Keep the first line under 72 characters
- Add a blank line and detailed explanation if needed
- Reference issue numbers if applicable (e.g., "Fix #123")

Examples:
```
Add docstrings to public API functions

Document all public functions in bfl/config.py with Google-style
docstrings including parameter and return type descriptions.
```

```
Fix solver error handling for invalid configs

Improve error messages when required champions are not found in
set data. Closes #456.
```

### PR Description

When creating a pull request, include:
- Clear description of changes
- Reference to related issues (if any)
- Testing performed
- Any breaking changes or migration notes

### Review Process

- All PRs require at least one approval before merging
- Ensure CI checks pass (tests, coverage, linting)
- Address review feedback promptly
- Keep PRs focused on a single feature or fix

## Project Structure

- `bfl/` - Core Bronze for Life solver logic
- `ui_api/` - FastAPI backend for web UI
- `frontend/` - React + TypeScript frontend
- `tests/` - Test suite (unit and integration)
- `docs/` - Additional documentation
- `examples/` - Example scripts and tutorials

## Getting Help

- Check existing documentation in `README.md` and `docs/`
- Review existing code for patterns and conventions
- Open an issue for questions or discussions

Thank you for contributing!
