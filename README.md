# tftcalcs

## Features

- Optimizes "Bronze for Life" trait activations using a beam-search solver that respects team size limits and trait blacklists.
- Loads official TFT set data from `data/en_us.json` with helper utilities for champions, traits, and breakpoints.
- Supports emblem modeling, including fixed starting emblems and optional automatic emblem assignment with configurable caps.
- Integrates MetaTFT stats (win rate, average placement, frequency) as a tie-breaker to prefer stronger lineups.
- Provides normalization and parsing helpers for MetaTFT unit data, including power calculations for each champion.
- Includes a command-line entry point (`bfl.bronze_for_life:main`) that prints optimized teams and trait summaries.
- Adds a Ryze-focused mode that counts only origin/region traits and requires Ryze by default on level 9 boards.
- Adds an itemization ranking mode that scores carry candidates by closeness to preferred items and trait fit.


## Tutorial: building Bronze for Life teams
Use the library or CLI to explore different emblem setups.

### Quickstart (no emblems)
```bash
python -m bfl.bronze_for_life
```
This runs the bundled solver with the default config: no emblems, MetaTFT weights if `data/metatft_units.txt` is present, and a team size of 9.

### Guided examples
An executable walk-through lives in `examples/bronze_for_life_tutorial.py`.
Run it from the repo root:
```bash
python examples/bronze_for_life_tutorial.py
```
It reuses the official set data (`data/en_us.json`) and MetaTFT paste (if present) to show four scenarios:
1. **No emblems** – pure Bronze for Life optimization.
2. **Two fixed emblems** – hard-code Zaun and Vanquisher emblems to see how the team shifts.
3. **Auto-select emblems** – let the solver choose up to two emblems to maximize bronze activations.
4. **Forced units** – lock in units (e.g., `TFT16_Tristana`, `TFT16_Lulu`) while still optimizing the rest of the team.

### Ryze mode (region traits only)
Ryze's "realm warp" scales with the number of active regions. Enable the Ryze mode by setting `"mode": "ryze"` in your config
or via the UI toggle. The solver will:

- Treat only the following origin traits as eligible: Bilgewater, Demacia, Freljord, Ionia, Ixtal, Noxus, Piltover, Shadow Isles,
  Shurima, Targon, Void, Yordle, Zaun.
- Default to `team_size = 9` (Ryze unlocks at level 9) unless you override it explicitly.
- Require `TFT16_Ryze` by default unless you explicitly set a different rule for him in `required_champions`.

Bronze-for-Life and Standard modes are unchanged; the Ryze constraints only apply when you select the new mode.

### Itemization mode (closest carries by item fit)
Itemization mode ranks carry candidates by how close they are to their ideal item builds. Provide available components
and completed items in `config.json` and set `"mode": "itemization"`. The solver will:

- Load item data from `data/en_us.json`.
- Resolve your available components and completed items by name or apiName.
- Normalize tutorial item apiName values (e.g., `TFTTutorial_Item_*`) to their standard counterparts.
- Score carry candidates by completed/craftable ideal items, then break ties with needed and existing team traits.

Relevant config fields:

- `available_components`: component items you currently have (names or apiName).
- `available_completed_items`: completed items already built (names or apiName).
- `team_traits`: traits already active on your team (tie-breaker).
- `needed_traits`: traits you want to add or reinforce (tie-breaker).
- `target_carries`: optional list of champion apiName values to rank.
- `allow_reforge`: whether completed items can count as reforged into another full item for scoring.

### Rolling your own setup
The tutorial script is a good template: it loads set data, builds the MetaTFT power map, and calls `solve_beam_search_bronze_with_emblems` with custom emblem inputs. Modify the `hard_emblems` map or `max_auto_emblems` value to model your own items, or pass `forced_units` (see `bfl/solver.py`) if you need specific champions locked in.

## Configuring runs with `config.json`
Defaults now live in a JSON-serializable `Config` object (see `bfl/config.py`). The CLI will automatically load `config.json` from the repo root when present; otherwise it falls back to the baked-in defaults. Use the helpers in `bfl/config_loader.py` to manage the file safely:

- `load_config(path)` – parse JSON (or return defaults when `path` is `None`).
- `save_config(config, path)` – write a config back to disk.
- `schemas/config_schema.json` – documents the expected JSON structure for UI validation.

Key fields mirror the previous module-level constants:

- **Paths**: `json_path` (set data) and `metatft_txt_path` (optional MetaTFT paste) point to your local files.
- **Problem size**: `team_size` and `beam_width` control roster length and search breadth.
- **Emblems**: `emblem_start_counts` declares fixed emblem counts; `max_emblems_total` lets the solver auto-assign up to N additional emblems.
- **Trait filtering**: `blacklist_traits_by_name` excludes traits from Bronze for Life even if active.
- **MetaTFT weighting**: `w_win`, `w_avg`, `w_freq` adjust how strongly live stats influence tie-breaks.

Edit `config.json` (or save a new file via `save_config`) then re-run `python -m bfl.bronze_for_life` or the tutorial script. The solver will keep the same defaults when no JSON is supplied.

### How a UI could integrate
A UI only needs to read and write `config.json` (or another path of its choosing) using the helpers in `bfl/config_loader.py`. Load the current settings with `load_config(path)`, surface the fields in your UI, then persist any changes with `save_config(config, path)`. To validate user input client-side, point your UI at `schemas/config_schema.json` for the expected shapes and types. The solver entry points will keep honoring defaults when the file is absent, so a UI can safely omit fields it does not expose.

## Running the Bronze for Life UI
The repository now ships with a lightweight FastAPI backend and a Vite + React + TypeScript frontend. Follow these steps even if you have never used JavaScript or React before:

1. **Install prerequisites.** Make sure you have recent versions of Python (for FastAPI) and Node.js + npm (for Vite). On most systems you can download Node.js from [nodejs.org](https://nodejs.org/) and Python from [python.org](https://www.python.org/downloads/).
2. **Create and activate a Python environment.** From the repository root run:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\\Scripts\\activate
   pip install -r requirements.txt
   ```
3. **Install frontend packages.** Still in the repository root, move into the UI folder and install dependencies:
   ```bash
   cd frontend
   npm install
   ```
4. **Start the API server.** From the repository root (activate your Python environment first if needed):
   ```bash
   uvicorn ui_api.main:app --reload --port 8000
   ```
   On Windows, if `uvicorn` is not found in your `PATH`, run the module directly instead:
   ```bash
   python -m uvicorn ui_api.main:app --reload --port 8000
   ```
   Leave this terminal window running so the API stays available.
5. **Start the React dev server.** Open a second terminal, return to the repository root, and run:
   ```bash
   cd frontend
   npm run dev
   ```
   The Vite server prints a local URL—by default `http://localhost:5173`.
6. **Open the UI.** Visit `http://localhost:5173` in your browser. The page will load the JSON schema and default solver config from the API, let you edit every field via a form, and offer a **Run solver** button. Keep both the API and Vite servers running while you experiment.

The UI now includes a dedicated **Itemization** tab that calls the versioned `/v2/itemization/*` API routes. Use that tab to enter your item inventory, select target carries, and view the closest builds without changing the comp finder configuration.

### Environment Configuration

You can customize the API and frontend configuration using environment variables. Copy `.env.example` to `.env` in the repository root and `frontend/.env.example` to `frontend/.env` to customize settings:

- **Backend**: 
  - `CORS_ORIGINS` - Configure allowed origins (comma-separated)
  - `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
  - `LOG_FORMAT` - Log format (json or simple)
  - `RATE_LIMIT_REQUESTS` - Requests per window (default: 100)
  - `RATE_LIMIT_WINDOW` - Rate limit window in seconds (default: 60)
  - `FILE_IO_MAX_RETRIES` - Maximum retry attempts for file operations (default: 3)
  - `FILE_IO_BACKOFF_BASE` - Base delay in seconds for exponential backoff (default: 0.1)
- **Frontend**: 
  - `VITE_API_BASE_URL` - Base URL for the backend API (default: http://localhost:8000)

See `.env.example` files for all available options and defaults.

## API Documentation

The FastAPI backend automatically generates OpenAPI/Swagger documentation. When the API server is running, you can access:

- **Swagger UI**: `http://localhost:8000/docs` - Interactive API documentation with try-it-out functionality
- **ReDoc**: `http://localhost:8000/redoc` - Alternative API documentation interface

### Main Endpoints

#### Solver Configuration Endpoints

- **`GET /schema`** - Get the JSON schema for solver configuration
  - Returns the schema used for validating configuration payloads
  - Useful for UI form generation and validation

- **`GET /config`** - Get the default solver configuration
  - Returns a complete configuration object with all default values
  - Can be used as a starting point for custom configurations

- **`POST /run`** - Execute the solver with a provided configuration
  - Accepts a JSON payload matching the schema from `/schema`
  - Returns solver results including team composition, trait counts, and metadata
  - Example:
    ```bash
    curl -X POST "http://localhost:8000/run" \
      -H "Content-Type: application/json" \
      -d '{"team_size": 9, "mode": "bronze"}'
    ```

#### Itemization Endpoints (v2)

- **`GET /v2/itemization/schema`** - Get the itemization schema
  - Returns versioned schema information for itemization mode

- **`GET /v2/itemization/config`** - Get default itemization configuration
  - Returns a versioned payload with default itemization settings
  - Includes mode set to "itemization"

- **`GET /v2/itemization/data`** - Get reference data for itemization UI
  - Returns available components, completed items, target carries, and traits
  - Useful for populating UI dropdowns and autocomplete fields

- **`POST /v2/itemization/run`** - Execute the itemization solver
  - Accepts a versioned payload with itemization configuration
  - Returns ranked carry candidates with item completion scores
  - Example:
    ```bash
    curl -X POST "http://localhost:8000/v2/itemization/run" \
      -H "Content-Type: application/json" \
      -d '{
        "version": 2,
        "config": {
          "available_components": ["TFT_Item_BFSword", "TFT_Item_RecurveBow"],
          "target_carries": ["TFT16_Jinx", "TFT16_Caitlyn"]
        }
      }'
    ```

### CORS Configuration

The API is configured to accept requests from `http://localhost:5173` (the default Vite dev server port) by default. For production deployments or custom configurations, you can set the `CORS_ORIGINS` environment variable to a comma-separated list of allowed origins. See `.env.example` for configuration examples.

### Error Handling

All endpoints return appropriate HTTP status codes:
- `200` - Success
- `400` - Bad Request (invalid configuration or validation errors)
- `500` - Internal Server Error (solver execution failures)

Error responses include detailed error messages and, for solver errors, debug logs and context information.

## Development and Testing

### Setting up the development environment

1. **Install development dependencies.** After setting up your Python environment, install the development packages:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Install pre-commit hooks** (optional but recommended):
   ```bash
   pre-commit install
   ```
   This will automatically run code quality checks (black, flake8, mypy) before each commit.

### Running tests

Run all tests with pytest:
```bash
pytest
```

Run tests with coverage reporting:
```bash
pytest --cov
```

View a detailed HTML coverage report:
```bash
pytest --cov
# Then open htmlcov/index.html in your browser
```

The project targets **90% code coverage** for `bfl/` and `ui_api/` packages. Coverage reports are generated in multiple formats:
- Terminal output showing missing lines
- HTML report in `htmlcov/` directory
- XML report in `coverage.xml` (for CI/CD integration)

### Test markers

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

### Code quality tools

- **black**: Code formatter (enforced via pre-commit hooks)
- **flake8**: Linter for PEP 8 compliance
- **mypy**: Static type checker
- **pre-commit**: Git hooks for automated quality checks

Run pre-commit checks manually on all files:
```bash
pre-commit run --all-files
```

### Integration tests

Integration tests are located in `tests/integration/` and cover:
- FastAPI endpoint testing (`test_api_flow.py`)
- End-to-end UI → API → Solver flow (`test_e2e.py`)
- Solver API integration (`test_solver_api.py`)
