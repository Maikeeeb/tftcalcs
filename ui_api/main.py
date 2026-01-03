"""FastAPI service exposing the Bronze for Life solver."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from jsonschema import ValidationError, validate

from bfl.champion_registry import list_playable_champions
from bfl.config import Config
from bfl.config_loader import (
    ConfigError,
    _load_int_map,
    _validate_int,
    apply_ryze_mode_defaults,
    _validate_required_champions,
    default_config,
    load_config,
)
from bfl.solver_api import SolverError, run_bfl

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "config_schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

app = FastAPI(title="Bronze for Life UI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _config_from_payload(payload: Mapping[str, Any]) -> Config:
    base = default_config()

    json_path = Path(payload.get("json_path", base.json_path)).expanduser()
    metatft_txt_path = Path(payload.get("metatft_txt_path", base.metatft_txt_path)).expanduser()
    metatft_traits_path = Path(payload.get("metatft_traits_path", base.metatft_traits_path)).expanduser()
    team_size_input = payload.get("team_size", base.team_size)
    team_size_provided = "team_size" in payload
    team_size = _validate_int("team_size", team_size_input, allow_negative=False)
    beam_width = _validate_int("beam_width", payload.get("beam_width", base.beam_width), allow_negative=False)
    max_emblems_total = _validate_int(
        "max_emblems_total", payload.get("max_emblems_total", base.max_emblems_total), allow_negative=False
    )

    blacklist_raw = payload.get("blacklist_traits_by_name", base.blacklist_traits_by_name)
    if isinstance(blacklist_raw, (set, list, tuple)):
        blacklist_traits_by_name = {str(t) for t in blacklist_raw}
    else:
        raise ConfigError("blacklist_traits_by_name must be a list of trait names.")

    emblem_start_counts = _load_int_map(
        payload.get("emblem_start_counts"), base.emblem_start_counts, name="emblem_start_counts", allow_negative=False
    )
    required_champions_raw = payload.get("required_champions")
    required_champions = _load_int_map(
        required_champions_raw,
        base.required_champions,
        name="required_champions",
        allowed_values={-1, 0, 1},
    )
    required_traits_min = _load_int_map(
        payload.get("required_traits_min"),
        base.required_traits_min,
        name="required_traits_min",
        allow_negative=False,
    )

    weights_raw = {
        "w_win": payload.get("w_win", base.w_win),
        "w_avg": payload.get("w_avg", base.w_avg),
        "w_freq": payload.get("w_freq", base.w_freq),
    }
    for name, value in weights_raw.items():
        if not isinstance(value, (int, float)):
            raise ConfigError(f"{name} must be numeric (got {type(value).__name__}).")

    set_id = str(payload.get("set_id", base.set_id))
    mode = str(payload.get("mode", base.mode))
    if mode not in {"bronze", "standard", "ryze"}:
        raise ConfigError("mode must be 'bronze', 'standard', or 'ryze'.")

    must_have_itemized_tank = payload.get("must_have_itemized_tank", base.must_have_itemized_tank)
    if not isinstance(must_have_itemized_tank, bool):
        raise ConfigError("must_have_itemized_tank must be a boolean.")

    team_size = apply_ryze_mode_defaults(
        mode,
        required_champions,
        required_payload=required_champions_raw if required_champions_raw is not None else None,
        team_size=team_size,
        team_size_provided=team_size_provided,
    )

    config = Config(
        json_path=json_path,
        set_id=set_id,
        metatft_txt_path=metatft_txt_path,
        metatft_traits_path=metatft_traits_path,
        team_size=team_size,
        beam_width=beam_width,
        blacklist_traits_by_name=blacklist_traits_by_name,
        emblem_start_counts=emblem_start_counts,
        max_emblems_total=max_emblems_total,
        required_champions=required_champions,
        required_traits_min=required_traits_min,
        w_win=float(weights_raw["w_win"]),
        w_avg=float(weights_raw["w_avg"]),
        w_freq=float(weights_raw["w_freq"]),
        mode=mode,
        must_have_itemized_tank=must_have_itemized_tank,
    )

    try:
        champs = list_playable_champions(json_path, set_id)
    except Exception as exc:  # pragma: no cover - defensive wrapper
        raise ConfigError(f"Failed to load champion list from {json_path} for set {set_id}: {exc}") from exc

    _validate_required_champions(config, champs)
    return config


@app.get("/schema")
def get_schema():
    """Return the JSON schema for solver configuration."""

    return SCHEMA


@app.get("/config")
def get_default_config():
    """Return the default solver configuration."""

    return load_config(None).to_dict()


@app.post("/run")
def run_solver(config: Mapping[str, Any]):
    """Validate the provided config and execute the solver."""

    try:
        validate(instance=config, schema=SCHEMA)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid configuration: {exc.message}") from exc

    try:
        solver_config = _config_from_payload(config)
        result = run_bfl(solver_config)
    except ConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SolverError as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": str(exc), "debug_log": exc.debug_log, "context": exc.context},
        ) from exc
    except Exception as exc:  # pragma: no cover - keep error surface concise
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return result
