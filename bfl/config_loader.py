from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, Mapping, Set

from bfl.config import Config, RYZE_API_NAME, default_config
from bfl.champion_registry import list_playable_champions


class ConfigError(ValueError):
    """Raised when configuration inputs are invalid."""


DEFAULT_CONFIG_FILENAME = "config.json"


def _validate_int(
    name: str, value, *, allow_negative: bool = False, allowed_values: Set[int] | None = None
) -> int:
    if not isinstance(value, int):
        raise ConfigError(f"{name} must be an integer (got {type(value).__name__}).")
    if allowed_values is not None:
        if value not in allowed_values:
            raise ConfigError(f"{name} must be one of {sorted(allowed_values)}, got {value}.")
        return value
    if not allow_negative and value < 0:
        raise ConfigError(f"{name} cannot be negative (got {value}).")
    return value


def _validate_bool(name: str, value) -> bool:
    if isinstance(value, bool):
        return value
    raise ConfigError(f"{name} must be a boolean (got {type(value).__name__}).")


def _validate_str_list(name: str, value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    raise ConfigError(f"{name} must be a list of strings.")


def _load_int_map(
    raw: Mapping | None,
    defaults: Dict[str, int],
    *,
    name: str,
    allow_negative: bool = False,
    allowed_values: Set[int] | None = None,
) -> Dict[str, int]:
    if raw is None:
        return dict(defaults)
    if not isinstance(raw, Mapping):
        raise ConfigError(f"{name} must be an object mapping strings to integers.")

    out = dict(defaults)
    for key, value in raw.items():
        out[key] = _validate_int(
            f"{name}['{key}']", value, allow_negative=allow_negative, allowed_values=allowed_values
        )
    return out


def _validate_required_champions(config: Config, champions: Iterable[str]) -> None:
    champ_set = set(champions)
    unknown_champs = [c for c in config.required_champions if c not in champ_set]
    if unknown_champs:
        raise ConfigError(f"Required champions not found in set data: {sorted(unknown_champs)}")


def apply_ryze_mode_defaults(
    mode: str,
    required_champions: Dict[str, int],
    *,
    required_payload: Mapping | None,
    team_size: int,
    team_size_provided: bool,
) -> int:
    """Adjust defaults for Ryze-centric mode without mutating other modes.

    The Ryze mode expects Ryze to be required by default and assumes a level-9
    board size unless the user overrides those values explicitly.
    """

    if mode != "ryze":
        return team_size

    if not team_size_provided:
        team_size = 9

    ryze_overridden = required_payload is not None and RYZE_API_NAME in required_payload
    if not ryze_overridden:
        required_champions[RYZE_API_NAME] = 1

    return team_size


def load_config(path: str | None) -> Config:
    """Load configuration from JSON or return defaults when ``path`` is ``None``.

    Missing fields fall back to the default configuration.
    """

    base = default_config()
    if path is None:
        return base

    cfg_path = Path(path)
    if not cfg_path.exists():
        raise ConfigError(f"Configuration file not found: {cfg_path}")

    with cfg_path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Invalid JSON in {cfg_path}: {exc}") from exc

    json_path = Path(data.get("json_path", base.json_path)).expanduser()
    metatft_txt_path = Path(data.get("metatft_txt_path", base.metatft_txt_path)).expanduser()
    metatft_traits_path = Path(
        data.get("metatft_traits_path", base.metatft_traits_path)
    ).expanduser()

    team_size_input = data.get("team_size", base.team_size)
    team_size_provided = "team_size" in data
    team_size = _validate_int("team_size", team_size_input, allow_negative=False)
    beam_width = _validate_int(
        "beam_width", data.get("beam_width", base.beam_width), allow_negative=False
    )
    max_emblems_total = _validate_int(
        "max_emblems_total",
        data.get("max_emblems_total", base.max_emblems_total),
        allow_negative=False,
    )

    blacklist_raw = data.get("blacklist_traits_by_name", base.blacklist_traits_by_name)
    if isinstance(blacklist_raw, (set, list, tuple)):
        blacklist_traits_by_name = {str(t) for t in blacklist_raw}
    else:
        raise ConfigError("blacklist_traits_by_name must be a list of trait names.")

    emblem_start_counts = _load_int_map(
        data.get("emblem_start_counts"),
        base.emblem_start_counts,
        name="emblem_start_counts",
        allow_negative=False,
    )
    required_champions_raw = data.get("required_champions")
    required_champions = _load_int_map(
        required_champions_raw,
        base.required_champions,
        name="required_champions",
        allowed_values={-1, 0, 1},
    )
    required_traits_min = _load_int_map(
        data.get("required_traits_min"),
        base.required_traits_min,
        name="required_traits_min",
        allow_negative=False,
    )

    weights_raw = {
        "w_win": data.get("w_win", base.w_win),
        "w_avg": data.get("w_avg", base.w_avg),
        "w_freq": data.get("w_freq", base.w_freq),
    }
    for name, value in weights_raw.items():
        if not isinstance(value, (int, float)):
            raise ConfigError(f"{name} must be numeric (got {type(value).__name__}).")

    set_id = str(data.get("set_id", base.set_id))
    mode = str(data.get("mode", base.mode))
    if mode not in {"bronze", "standard", "ryze", "itemization"}:
        raise ConfigError(
            f"mode must be 'bronze', 'standard', 'ryze', or 'itemization' (got {mode})."
        )

    team_size = apply_ryze_mode_defaults(
        mode,
        required_champions,
        required_payload=required_champions_raw if required_champions_raw is not None else None,
        team_size=team_size,
        team_size_provided=team_size_provided,
    )

    must_have_itemized_tank = _validate_bool(
        "must_have_itemized_tank", data.get("must_have_itemized_tank", base.must_have_itemized_tank)
    )
    seed_verticals = _validate_bool(
        "seed_verticals", data.get("seed_verticals", base.seed_verticals)
    )
    available_components = _validate_str_list(
        "available_components", data.get("available_components", base.available_components)
    )
    available_completed_items = _validate_str_list(
        "available_completed_items",
        data.get("available_completed_items", base.available_completed_items),
    )
    target_carries = _validate_str_list(
        "target_carries", data.get("target_carries", base.target_carries)
    )
    team_traits = _validate_str_list("team_traits", data.get("team_traits", base.team_traits))
    needed_traits = _validate_str_list(
        "needed_traits", data.get("needed_traits", base.needed_traits)
    )
    allow_reforge = _validate_bool("allow_reforge", data.get("allow_reforge", base.allow_reforge))

    if not available_components and "itemization_components" in data:
        available_components = _validate_str_list(
            "itemization_components", data.get("itemization_components")
        )
    if not available_completed_items and "itemization_completed_items" in data:
        available_completed_items = _validate_str_list(
            "itemization_completed_items", data.get("itemization_completed_items")
        )
    if not target_carries and "itemization_candidate_champions" in data:
        target_carries = _validate_str_list(
            "itemization_candidate_champions", data.get("itemization_candidate_champions")
        )
    if not team_traits and "itemization_team_traits" in data:
        team_traits = _validate_str_list(
            "itemization_team_traits", data.get("itemization_team_traits")
        )
    if not needed_traits and "itemization_needed_traits" in data:
        needed_traits = _validate_str_list(
            "itemization_needed_traits", data.get("itemization_needed_traits")
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
        seed_verticals=seed_verticals,
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


def save_config(config: Config, path: str):
    """Save configuration to a JSON file.

    Creates parent directories if needed and writes the config in JSON format
    with indentation and sorted keys.

    Parameters
    ----------
    config : Config
        Configuration object to save.
    path : str
        File path where the configuration will be written.

    Raises
    ------
    OSError
        If the file cannot be written (e.g., permission denied).
    """
    cfg_path = Path(path)
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    with cfg_path.open("w", encoding="utf-8") as f:
        json.dump(config.to_dict(), f, indent=2, sort_keys=True)


def validate_config_against_data(
    config: Config, champions: Iterable[str], trait_breakpoints: Mapping[str, object]
) -> None:
    """Validate configuration against loaded set data.

    Checks that all referenced champions, traits, and constraints are valid
    according to the provided set data. Raises ConfigError if any invalid
    references are found.

    Parameters
    ----------
    config : Config
        Configuration to validate.
    champions : Iterable[str]
        List of valid champion apiNames from set data.
    trait_breakpoints : Mapping[str, object]
        Dictionary of trait names to breakpoint data from set data.

    Raises
    ------
    ConfigError
        If any required champions, traits, or other config values are invalid
        (not found in set data, negative when not allowed, or zero/negative
        team_size/beam_width).
    """
    _validate_required_champions(config, champions)
    champ_set = set(champions)
    trait_set = set(trait_breakpoints)

    invalid_req_traits = [t for t in config.required_traits_min if t not in trait_set]
    if invalid_req_traits:
        raise ConfigError(f"Required traits not found in set data: {sorted(invalid_req_traits)}")

    invalid_emblem_traits = [t for t in config.emblem_start_counts if t not in trait_set]
    if invalid_emblem_traits:
        raise ConfigError(f"Emblem traits not found in set data: {sorted(invalid_emblem_traits)}")

    invalid_blacklist = [t for t in config.blacklist_traits_by_name if t not in trait_set]
    if invalid_blacklist:
        raise ConfigError(f"Blacklisted traits not found in set data: {sorted(invalid_blacklist)}")

    invalid_team_traits = [t for t in config.team_traits if t not in trait_set]
    if invalid_team_traits:
        raise ConfigError(f"Team traits not found in set data: {sorted(invalid_team_traits)}")

    invalid_needed_traits = [t for t in config.needed_traits if t not in trait_set]
    if invalid_needed_traits:
        raise ConfigError(f"Needed traits not found in set data: {sorted(invalid_needed_traits)}")

    invalid_candidates = [champ for champ in config.target_carries if champ not in champ_set]
    if invalid_candidates:
        raise ConfigError(f"Target carries not found in set data: {sorted(invalid_candidates)}")

    negative_emblems = {t: v for t, v in config.emblem_start_counts.items() if v < 0}
    if negative_emblems:
        raise ConfigError(f"Emblem counts cannot be negative: {negative_emblems}")

    negative_required = {t: v for t, v in config.required_traits_min.items() if v < 0}
    if negative_required:
        raise ConfigError(f"Trait minimums cannot be negative: {negative_required}")

    if config.team_size <= 0:
        raise ConfigError(f"team_size must be positive (got {config.team_size}).")

    if config.beam_width <= 0:
        raise ConfigError(f"beam_width must be positive (got {config.beam_width}).")
