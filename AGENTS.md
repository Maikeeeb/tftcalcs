# Repository-wide agent guidelines

- **Scope:** This file applies to the entire repository.
- **Bronze for Life CLI:** Run via `python -m bfl.bronze_for_life`.
- **Tutorial:** See `examples/bronze_for_life_tutorial.py` for a walkthrough of CLI usage.
- **Configuration:** Configuration files live in `config.json` and `config_schema.json`; helpers are in `bfl/config_loader.py`.
- **UI workflow:**
  1. Create/activate a Python venv and install FastAPI dependencies.
  2. Run `npm install` in the `frontend` directory.
  3. Start the API with `uvicorn ui_api.main:app --reload --port 8000`.
- **Data awareness:** Check `en_us.json` and the MetaTFT text files (`metatft_units.txt`, `metatft_traits.txt`) when making related changes.
- **Coding conventions:** Follow both Python and TypeScript standards as appropriate.
- **Documentation:** Add or update references in `/docs/` and `readme.md` so future work remains understandable.
