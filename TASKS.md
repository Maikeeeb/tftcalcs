# UI readiness tasks (JSON config, manual emblem/trait control)

The list below updates the earlier suggestions to match the requested constraints:
- **JSON only** for persisted config (no YAML).
- **Champion options auto-generated** from `en_us.json`, while **emblem/trait tracking stays manual** (but can be overridden in JSON if desired).
- **CLI output unchanged**; a UI-friendly API runs alongside it.

## 1) Config object with JSON load/save
- Create a `Config` dataclass (or similar) in `bfl/config.py` (or a new module) mirroring current defaults: paths, team size, beam width, emblem limits, required champions/traits, and weights.
- Implement `from_json(path: str | None)`/`to_json(path: str)` helpers that fall back to defaults when the file is missing or fields are absent.
- Validate inputs (e.g., negative counts, unknown champions/traits) and return structured errors the UI can surface.
- Update `bfl/bronze_for_life.py` to consume a `Config` instance; when no config is provided, it should behave exactly like today.

## 2) Champion options derived from set data (traits/emblems stay manual)
- Add a helper in `bfl.set_loader` (or a nearby module) that, given `set_data`, returns the valid champion API names and the traits that are associated with multiple champions.
- Replace the hard-coded champion dicts in config with generation seeded from the loader while keeping emblem/trait requirements manually specified (but overridable via JSON).
- Expose a function like `list_playable_options()` for the UI to populate dropdowns (champion names plus manually curated emblem/trait options).
- Cover this generation with unit tests using the current `en_us.json`.

## 3) UI-friendly solver API alongside the CLI
- Extract the core solve path from `bfl/bronze_for_life.main` into a callable such as `run_bfl(config)` that returns structured data: team roster, trait counts/tiers, emblem usage, and MetaTFT stats.
- Keep the existing console behavior by having the CLI wrapper call this function and pretty-print the same output as today.
- Document the returned schema so the UI can render labels now and images later.
- Add tests asserting the returned structure contains the expected keys and mirrors the printed output for a sample config.

## 4) Examples
- Provide a small example JSON config showing defaults plus optional overrides (including manual emblem/trait tweaks) to guide both CLI users and a future UI.
