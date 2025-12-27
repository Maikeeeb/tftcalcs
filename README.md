# tftcalcs

## Features

- Optimizes "Bronze for Life" trait activations using a beam-search solver that respects team size limits and trait blacklists.
- Loads official TFT set data from `en_us.json` with helper utilities for champions, traits, and breakpoints.
- Supports emblem modeling, including fixed starting emblems and optional automatic emblem assignment with configurable caps.
- Integrates MetaTFT stats (win rate, average placement, frequency) as a tie-breaker to prefer stronger lineups.
- Provides normalization and parsing helpers for MetaTFT unit data, including power calculations for each champion.
- Includes a command-line entry point (`bfl.bronze_for_life:main`) that prints optimized teams and trait summaries.


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

### Rolling your own setup
The tutorial script is a good template: it loads set data, builds the MetaTFT power map, and calls `solve_beam_search_bronze_with_emblems` with custom emblem inputs. Modify the `hard_emblems` map or `max_auto_emblems` value to model your own items, or pass `forced_units` (see `bfl/solver.py`) if you need specific champions locked in.

## Configuring runs with `config.py`
The library pulls its defaults from `bfl/config.py` so you can centralize adjustments without editing the solver code:

- **Paths**: `JSON_PATH` (set data) and `METATFT_TXT_PATH` (optional MetaTFT paste) can be pointed to your own files.
- **Problem size**: `TEAM_SIZE` and `BEAM_WIDTH` control roster length and search breadth.
- **Emblems**: `EMBLEM_START_COUNTS` declares hard-coded emblem counts; `MAX_EMBLEMS_TOTAL` lets the solver auto-assign up to N additional emblems from the eligible trait pool.
- **Trait filtering**: `BLACKLIST_TRAITS_BY_NAME` excludes traits from Bronze for Life eligibility even if active.
- **MetaTFT weighting**: `W_WIN`, `W_AVG`, `W_FREQ` adjust how strongly live stats influence tie-breaks.

To tweak a run, edit `config.py` then re-execute either `python -m bfl.bronze_for_life` or `python examples/bronze_for_life_tutorial.py`. The tutorial also shows how to pass per-invocation overrides (for emblems and forced units) if you prefer not to change the shared config.
