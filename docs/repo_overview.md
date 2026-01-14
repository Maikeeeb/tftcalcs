# Repository overview and developer guide

This document summarizes the codebase structure, runtime data flow, and entry points so new contributors or coding agents can quickly locate behavior.

## Data files and schemas
- **Set data** comes from `data/en_us.json`, whose champions/traits are filtered by `bfl.set_loader.load_set_data` when assembling the playable pool.
- **MetaTFT pastes** in `data/metatft_units.txt` and `data/metatft_traits.txt` are optional but enable power/tank classification, trait scoring, and quality heuristics. When absent, the solver falls back to neutral weights.
- **Configuration schema** lives in `schemas/config_schema.json` and mirrors the `bfl.config.Config` dataclass. The FastAPI service validates requests against this schema and the frontend form is generated from it.

## Python package layout (`bfl/`)
- **Configuration (`config.py`, `config_loader.py`)** defines the `Config` dataclass, default paths, emblem seeds, required-champion flags, and helper loaders/savers. Validation helpers ensure integer maps, champion rules, and file paths are well-formed before a run.
- **Set + MetaTFT ingestion (`set_loader.py`, `metatft.py`, `champion_registry.py`)** normalizes Riot set data, builds champion → trait maps, classifies eligible traits, and converts MetaTFT pastes into unit/trait power stats. Tank candidates are detected from item builds to enforce the optional “must have itemized tank” constraint.
- **Trait helpers (`traits.py`)** add champion trait counts, apply starting emblem offsets, and mark eligible traits used by the solver.
- **Solver core** is split across multiple modules:
  - `beam_search.py` - Core beam search algorithm with state expansion and pruning
  - `scoring.py` - Scoring functions (bronze piecewise, quality evaluation, trait scores, fake bronze penalties)
  - `team_builder.py` - Team building utilities (requirement checking, feasibility, effective counts)
  - `solver.py` - Re-exports for backward compatibility; new code should import from the specific modules
- **Vertical seeding** (`seed_verticals`): When enabled, the initial beam is pre-seeded with teams targeting the highest reachable breakpoint for each eligible trait. For each trait, the algorithm identifies champions that contribute to that trait and builds partial teams aiming for the trait's maximum breakpoint. This helps the search consider far-off breakpoints (e.g., Void 9, Ionia 9) even when early partial teams have low scores. Most useful when searching for high-tier trait activations.
- **Itemization solver (`itemization_solver.py`)** ranks carry candidates by how close they are to preferred item builds and breaks ties with team/needed trait fit. It loads item data from `data/en_us.json`, resolves available components/completed items (including normalizing tutorial item apiName aliases), and supports optional reforging heuristics.
- **Public API (`solver_api.py`)** orchestrates one end-to-end solve: it loads set/MetaTFT data, builds power maps and trait stats, validates config, and calls either the Bronze-for-Life solver or the itemization ranking solver based on mode. Structured results include context, meta weighting details, trait counts, and requirement satisfaction. Errors include a decision log for debugging.
- **CLI entrypoint (`bronze_for_life.py`)** resolves config from CLI arguments or `config.json`, runs `run_bfl`, and prints team composition, bronze/upgraded trait breakdowns, emblem usage, and ineligible traits to stdout for quick inspection.

## UI API (`ui_api/main.py`)
- FastAPI service exposing three routes: `/schema` (returns the JSON schema), `/config` (returns default config), and `/run` (validates a posted config and executes the solver). Versioned itemization routes live under `/v2/itemization/*` and serve reference data, config, and solver execution for the itemization UI.
- CORS is enabled for the Vite dev server, so the React frontend can post solver runs locally without extra setup.

## Frontend (`frontend/`)
- Vite + React + TypeScript app in `frontend/src`. `App.tsx` loads the schema/config via `@tanstack/react-query`, renders a `@rjsf` (JSONSchema) form, and adds helper controls for Bronze vs Standard mode and the “must have itemized tank” toggle. Submissions call the FastAPI `/run` endpoint and render results or debug logs via dedicated components (`ResultsSection`, `DebugLogCard`, `Loader`).
- Custom form fields (`components/MappingField.tsx` and related assets) provide searchable mapping inputs for emblems, trait minimums, and champion requirements with unlockable-value hints and cost coloring.
- Shared type definitions live in `frontend/src/types.ts`, reusable utilities in `frontend/src/utils/`, and styling in `frontend/src/index.css`. Tests live alongside components in `frontend/src/__tests__/`.

## Examples and supporting files
- `examples/bronze_for_life_tutorial.py` demonstrates multiple solver scenarios (no emblems, fixed emblems, auto-emblems, forced units) and is a good template for new integrations.
- `TASKS.md` and existing docs (`docs/bronze_for_life.md`, `docs/ryze_constraints.md`) capture historical solver behavior notes.
- `utils/tft_teamplanner_code.py`, `utils/tft_set16_teamplanner_mapping.json`, and `frontend/src/teamPlanner.ts` hold mapping logic for a separate team-planner helper, while `img/` stores downloaded static assets used by the UI.
