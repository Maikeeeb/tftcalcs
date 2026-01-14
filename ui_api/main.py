"""FastAPI service exposing the Bronze for Life solver."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Mapping

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from jsonschema import ValidationError, validate

from bfl.champion_registry import list_playable_champions
from bfl.config import Config
from bfl.config_loader import (
    ConfigError,
    _load_int_map,
    _validate_int,
    _validate_str_list,
    apply_ryze_mode_defaults,
    _validate_required_champions,
    default_config,
    load_config,
)
from bfl.itemization_solver import CARRY_ITEM_PREFERENCES, load_item_catalog
from bfl.set_loader import load_set_data
from bfl.solver_api import SolverError, run_solver as solve_config
from ui_api.logging_config import setup_logging

# Setup logging
api_logger, _ = setup_logging()

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "config_schema.json"
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
ITEMIZATION_VERSION = 2

# CORS configuration: read from environment variable or default to localhost:5173
# For production, set CORS_ORIGINS to a comma-separated list of allowed origins
_cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173")
CORS_ORIGINS = [origin.strip() for origin in _cors_origins_env.split(",") if origin.strip()]

app = FastAPI(title="Bronze for Life UI API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        start_time = time.time()
        method = request.method
        path = request.url.path

        # Log request
        api_logger.info(f"Request: {method} {path}")

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            status_code = response.status_code

            # Log response based on status code
            if status_code < 400:
                api_logger.info(f"Response: {method} {path} - {status_code} ({duration_ms:.1f}ms)")
            elif status_code < 500:
                api_logger.warning(
                    f"Response: {method} {path} - {status_code} ({duration_ms:.1f}ms)"
                )
            else:
                api_logger.error(f"Response: {method} {path} - {status_code} ({duration_ms:.1f}ms)")

            return response
        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            api_logger.error(
                f"Exception: {method} {path} - {type(exc).__name__}: {exc} ({duration_ms:.1f}ms)",
                exc_info=True,
            )
            raise


app.add_middleware(RequestLoggingMiddleware)


def _config_from_payload(payload: Mapping[str, Any]) -> Config:
    base = default_config()

    json_path = Path(payload.get("json_path", base.json_path)).expanduser()
    metatft_txt_path = Path(payload.get("metatft_txt_path", base.metatft_txt_path)).expanduser()
    metatft_traits_path = Path(
        payload.get("metatft_traits_path", base.metatft_traits_path)
    ).expanduser()
    team_size_input = payload.get("team_size", base.team_size)
    team_size_provided = "team_size" in payload
    team_size = _validate_int("team_size", team_size_input, allow_negative=False)
    beam_width = _validate_int(
        "beam_width", payload.get("beam_width", base.beam_width), allow_negative=False
    )
    max_emblems_total = _validate_int(
        "max_emblems_total",
        payload.get("max_emblems_total", base.max_emblems_total),
        allow_negative=False,
    )

    blacklist_raw = payload.get("blacklist_traits_by_name", base.blacklist_traits_by_name)
    if isinstance(blacklist_raw, (set, list, tuple)):
        blacklist_traits_by_name = {str(t) for t in blacklist_raw}
    else:
        raise ConfigError("blacklist_traits_by_name must be a list of trait names.")

    emblem_start_counts = _load_int_map(
        payload.get("emblem_start_counts"),
        base.emblem_start_counts,
        name="emblem_start_counts",
        allow_negative=False,
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
    if mode not in {"bronze", "standard", "ryze", "itemization"}:
        raise ConfigError("mode must be 'bronze', 'standard', 'ryze', or 'itemization'.")

    must_have_itemized_tank = payload.get("must_have_itemized_tank", base.must_have_itemized_tank)
    if not isinstance(must_have_itemized_tank, bool):
        raise ConfigError("must_have_itemized_tank must be a boolean.")

    available_components = _validate_str_list(
        "available_components", payload.get("available_components", base.available_components)
    )
    available_completed_items = _validate_str_list(
        "available_completed_items",
        payload.get("available_completed_items", base.available_completed_items),
    )
    target_carries = _validate_str_list(
        "target_carries", payload.get("target_carries", base.target_carries)
    )
    team_traits = _validate_str_list("team_traits", payload.get("team_traits", base.team_traits))
    needed_traits = _validate_str_list(
        "needed_traits", payload.get("needed_traits", base.needed_traits)
    )
    allow_reforge = payload.get("allow_reforge", base.allow_reforge)
    if not isinstance(allow_reforge, bool):
        raise ConfigError("allow_reforge must be a boolean.")

    if not available_components and "itemization_components" in payload:
        available_components = _validate_str_list(
            "itemization_components", payload.get("itemization_components")
        )
    if not available_completed_items and "itemization_completed_items" in payload:
        available_completed_items = _validate_str_list(
            "itemization_completed_items", payload.get("itemization_completed_items")
        )
    if not target_carries and "itemization_candidate_champions" in payload:
        target_carries = _validate_str_list(
            "itemization_candidate_champions", payload.get("itemization_candidate_champions")
        )
    if not team_traits and "itemization_team_traits" in payload:
        team_traits = _validate_str_list(
            "itemization_team_traits", payload.get("itemization_team_traits")
        )
    if not needed_traits and "itemization_needed_traits" in payload:
        needed_traits = _validate_str_list(
            "itemization_needed_traits", payload.get("itemization_needed_traits")
        )

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
        available_components=available_components,
        available_completed_items=available_completed_items,
        target_carries=target_carries,
        team_traits=team_traits,
        needed_traits=needed_traits,
        allow_reforge=allow_reforge,
    )

    try:
        champs = list_playable_champions(json_path, set_id)
    except Exception as exc:  # pragma: no cover - defensive wrapper
        raise ConfigError(
            f"Failed to load champion list from {json_path} for set {set_id}: {exc}"
        ) from exc

    _validate_required_champions(config, champs)
    return config


def _normalize_config_payload(payload: Mapping[str, Any] | Config) -> Mapping[str, Any]:
    if isinstance(payload, Config):
        return payload.to_dict()
    return payload


def _versioned_config_payload(payload: Mapping[str, Any]) -> Config:
    if not isinstance(payload, Mapping):
        raise ConfigError("Payload must be an object.")
    version = payload.get("version")
    if version != ITEMIZATION_VERSION:
        raise ConfigError(f"Expected payload version {ITEMIZATION_VERSION}.")
    config = payload.get("config")
    if isinstance(config, Config):
        config = config.to_dict()
    if not isinstance(config, Mapping):
        raise ConfigError("Payload must include a 'config' object.")
    return _config_from_payload(config)


def _itemization_reference_data(config: Config) -> dict[str, object]:
    catalog = load_item_catalog(config.json_path)
    set_data, _, champ_traits, _, _, _, _ = load_set_data(config.json_path, config.set_id)
    champ_name_map = {
        champ.get("apiName"): champ.get("name", champ.get("apiName"))
        for champ in set_data.get("champions", [])
        if champ.get("apiName")
    }
    components = [
        {"apiName": api, "name": catalog.items_by_api[api].get("name", api)}
        for api in sorted(catalog.component_api_names)
    ]
    completed = [
        {
            "apiName": api,
            "name": catalog.items_by_api[api].get("name", api),
            "components": list(catalog.compositions.get(api, ())),
        }
        for api in sorted(catalog.craftable_api_names)
    ]
    carry_pool = [
        {
            "apiName": champ,
            "name": champ_name_map.get(champ, champ),
            "traits": champ_traits.get(champ, []),
        }
        for champ in sorted(set(CARRY_ITEM_PREFERENCES) & set(champ_traits))
    ]
    traits = sorted({trait for traits in champ_traits.values() for trait in traits})
    return {
        "components": components,
        "completed_items": completed,
        "target_carries": carry_pool,
        "traits": traits,
    }


@app.get("/schema")
def get_schema():
    """Return the JSON schema for solver configuration."""

    return SCHEMA


@app.get("/config")
def get_default_config():
    """Return the default solver configuration."""

    return load_config(None).to_dict()


@app.post("/run")
def run_solver_endpoint(config: Mapping[str, Any]):
    """Validate the provided config and execute the solver."""

    try:
        payload = _normalize_config_payload(config)
        validate(instance=payload, schema=SCHEMA)
    except ValidationError as exc:
        api_logger.warning(f"Schema validation failed: {exc.message}")
        raise HTTPException(
            status_code=400, detail=f"Invalid configuration: {exc.message}"
        ) from exc

    try:
        solver_config = _config_from_payload(payload)
        api_logger.info(
            f"Running solver with mode={solver_config.mode}, team_size={solver_config.team_size}"
        )
        result = solve_config(solver_config)
        api_logger.info("Solver completed successfully")
    except ConfigError as exc:
        api_logger.warning(f"Configuration error: {exc}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SolverError as exc:
        api_logger.error(f"Solver error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": str(exc), "debug_log": exc.debug_log, "context": exc.context},
        ) from exc
    except Exception as exc:  # pragma: no cover - keep error surface concise
        api_logger.error(f"Unexpected error in solver endpoint: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return result


@app.get("/v2/itemization/schema")
def get_itemization_schema():
    """Return the JSON schema for itemization configuration."""

    return {"version": ITEMIZATION_VERSION, "schema": SCHEMA}


@app.get("/v2/itemization/config")
def get_itemization_config():
    """Return the default itemization configuration."""

    config = load_config(None)
    config.mode = "itemization"
    return {"version": ITEMIZATION_VERSION, "config": config.to_dict()}


@app.get("/v2/itemization/data")
def get_itemization_reference():
    """Return reference data for itemization UI controls."""

    config = load_config(None)
    return {"version": ITEMIZATION_VERSION, "data": _itemization_reference_data(config)}


@app.post("/v2/itemization/run")
def run_itemization(payload: Mapping[str, Any]):
    """Validate a versioned payload and execute the itemization solver."""

    try:
        if not isinstance(payload, Mapping):
            raise ConfigError("Payload must be an object.")
        raw_config = payload.get("config")
        if not isinstance(raw_config, Mapping):
            raise ConfigError("Payload must include a 'config' object.")
        validate(instance=raw_config, schema=SCHEMA)
        solver_config = _versioned_config_payload(payload)
        solver_config.mode = "itemization"
        api_logger.info(
            f"Running itemization solver with {len(solver_config.target_carries)} target carries"
        )
        result = solve_config(solver_config)
        api_logger.info("Itemization solver completed successfully")
    except ValidationError as exc:
        api_logger.warning(f"Itemization schema validation failed: {exc.message}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid configuration for version {ITEMIZATION_VERSION}: {exc.message}",
        ) from exc
    except ConfigError as exc:
        api_logger.warning(f"Itemization configuration error: {exc}")
        raise HTTPException(
            status_code=400, detail=f"Version {ITEMIZATION_VERSION} config error: {exc}"
        ) from exc
    except SolverError as exc:
        api_logger.error(f"Itemization solver error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": str(exc), "debug_log": exc.debug_log, "context": exc.context},
        ) from exc
    except Exception as exc:  # pragma: no cover - keep error surface concise
        api_logger.error(f"Unexpected error in itemization endpoint: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"version": ITEMIZATION_VERSION, "result": result}
