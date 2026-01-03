# tftcalcs

## Features

- Optimizes "Bronze for Life" trait activations using a beam-search solver that respects team size limits and trait blacklists.
- Loads official TFT set data from `en_us.json` with helper utilities for champions, traits, and breakpoints.
- Supports emblem modeling, including fixed starting emblems and optional automatic emblem assignment with configurable caps.
- Integrates MetaTFT stats (win rate, average placement, frequency) as a tie-breaker to prefer stronger lineups.
- Provides normalization and parsing helpers for MetaTFT unit data, including power calculations for each champion.
- Includes a command-line entry point (`bfl.bronze_for_life:main`) that prints optimized teams and trait summaries.
- Adds a Ryze-focused mode that counts only origin/region traits and requires Ryze by default on level 9 boards.


## Tutorial: building Bronze for Life teams
Use the library or CLI to explore different emblem setups.

### Quickstart (no emblems)
```bash
python -m bfl.bronze_for_life
```
This runs the bundled solver with the default config: no emblems, MetaTFT weights if `metatft_units.txt` is present, and a team size of 9.

### Guided examples
An executable walk-through lives in `examples/bronze_for_life_tutorial.py`.
Run it from the repo root:
```bash
python examples/bronze_for_life_tutorial.py
```
It reuses the official set data (`en_us.json`) and MetaTFT paste (if present) to show four scenarios:
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

### Rolling your own setup
The tutorial script is a good template: it loads set data, builds the MetaTFT power map, and calls `solve_beam_search_bronze_with_emblems` with custom emblem inputs. Modify the `hard_emblems` map or `max_auto_emblems` value to model your own items, or pass `forced_units` (see `bfl/solver.py`) if you need specific champions locked in.

## Configuring runs with `config.json`
Defaults now live in a JSON-serializable `Config` object (see `bfl/config.py`). The CLI will automatically load `config.json` from the repo root when present; otherwise it falls back to the baked-in defaults. Use the helpers in `bfl/config_loader.py` to manage the file safely:

- `load_config(path)` – parse JSON (or return defaults when `path` is `None`).
- `save_config(config, path)` – write a config back to disk.
- `config_schema.json` – documents the expected JSON structure for UI validation.

Key fields mirror the previous module-level constants:

- **Paths**: `json_path` (set data) and `metatft_txt_path` (optional MetaTFT paste) point to your local files.
- **Problem size**: `team_size` and `beam_width` control roster length and search breadth.
- **Emblems**: `emblem_start_counts` declares fixed emblem counts; `max_emblems_total` lets the solver auto-assign up to N additional emblems.
- **Trait filtering**: `blacklist_traits_by_name` excludes traits from Bronze for Life even if active.
- **MetaTFT weighting**: `w_win`, `w_avg`, `w_freq` adjust how strongly live stats influence tie-breaks.

Edit `config.json` (or save a new file via `save_config`) then re-run `python -m bfl.bronze_for_life` or the tutorial script. The solver will keep the same defaults when no JSON is supplied.

### How a UI could integrate
A UI only needs to read and write `config.json` (or another path of its choosing) using the helpers in `bfl/config_loader.py`. Load the current settings with `load_config(path)`, surface the fields in your UI, then persist any changes with `save_config(config, path)`. To validate user input client-side, point your UI at `config_schema.json` for the expected shapes and types. The solver entry points will keep honoring defaults when the file is absent, so a UI can safely omit fields it does not expose.

## Running the Bronze for Life UI
The repository now ships with a lightweight FastAPI backend and a Vite + React + TypeScript frontend. Follow these steps even if you have never used JavaScript or React before:

1. **Install prerequisites.** Make sure you have recent versions of Python (for FastAPI) and Node.js + npm (for Vite). On most systems you can download Node.js from [nodejs.org](https://nodejs.org/) and Python from [python.org](https://www.python.org/downloads/).
2. **Create and activate a Python environment.** From the repository root run:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\\Scripts\\activate
   pip install fastapi uvicorn jsonschema
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
