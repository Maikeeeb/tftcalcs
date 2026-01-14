"""Structured API for running Bronze for Life solver."""

import json
from pathlib import Path
from typing import Dict, List, Mapping, Set

from bfl.config import Config, REPO_ROOT
from bfl.config_loader import DEFAULT_CONFIG_FILENAME, load_config, validate_config_against_data
from bfl.metatft import (
    best_trait_stat,
    build_name_to_api_map,
    classify_tank_champions,
    load_metatft_txt,
    metatft_to_unit_stats,
    metatft_to_trait_stats,
    normalize_name,
    parse_metatft_units,
    trait_power,
    unit_power,
)
from bfl.itemization_solver import ItemizationError, run_itemization_solver
from bfl.set_loader import load_set_data
from bfl.solver import solve_beam_search_bronze_with_emblems
from bfl.traits import apply_emblem_starts, classify_traits

__all__ = [
    "build_name_to_api_map",
    "load_set_data",
    "load_metatft_txt",
    "metatft_to_unit_stats",
    "metatft_to_trait_stats",
    "normalize_name",
    "parse_metatft_units",
    "region_trait_pool",
    "solve_beam_search_bronze_with_emblems",
    "unit_power",
    "trait_power",
    "apply_emblem_starts",
    "classify_traits",
    "run_bfl",
    "run_solver",
]


class SolverError(RuntimeError):
    """Raised when solver execution fails but a debug log is available."""

    def __init__(self, message: str, debug_log: List[str], context: Dict[str, object]):
        super().__init__(message)
        self.debug_log = debug_log
        self.context = context


BARON_API_NAME = "TFT16_BaronNashor"

SPECIAL_CHAMPION_SLOT_SIZES = {BARON_API_NAME: 2}
SPECIAL_TRAIT_VALUE_OVERRIDES = {BARON_API_NAME: {"Void": 2}}
REGION_TRAITS = (
    "Bilgewater",
    "Demacia",
    "Freljord",
    "Ionia",
    "Ixtal",
    "Noxus",
    "Piltover",
    "Shadow Isles",
    "Shurima",
    "Targon",
    "Void",
    "Yordle",
    "Zaun",
)


def _resolve_config(config: Config | None, config_path: str | None) -> Config:
    if config is not None:
        return config

    default_path = Path(config_path) if config_path else REPO_ROOT / DEFAULT_CONFIG_FILENAME
    if config_path or default_path.exists():
        return load_config(str(default_path))

    return load_config(None)


def region_trait_pool(trait_breakpoints: Mapping[str, object]) -> Set[str]:
    """Return traits that represent regions and exist in the current set."""

    return {trait for trait in REGION_TRAITS if trait in trait_breakpoints}


def _build_requirement_details(
    team: List[str], counts: Dict[str, int], config: Config, tank_champions: set[str] | None
) -> Dict[str, object]:
    champion_requirements: Dict[str, Dict[str, object]] = {}
    for champ, flag in config.required_champions.items():
        status = "ignored"
        present = champ in team
        satisfied = True
        if flag > 0:
            status = "required"
            satisfied = present
        elif flag < 0:
            status = "banned"
            satisfied = not present
        champion_requirements[champ] = {
            "rule": flag,
            "present": present,
            "status": status,
            "satisfied": satisfied,
        }

    trait_requirements: Dict[str, Dict[str, object]] = {}
    for trait, minimum in config.required_traits_min.items():
        trait_requirements[trait] = {
            "minimum": minimum,
            "actual": counts.get(trait, 0),
            "satisfied": counts.get(trait, 0) >= minimum,
        }

    tank_requirement = None
    if config.must_have_itemized_tank:
        has_tank = bool(set(team) & (tank_champions or set()))
        tank_requirement = {
            "required": True,
            "candidates": sorted(tank_champions or []),
            "satisfied": has_tank,
        }

    all_satisfied = all(detail["satisfied"] for detail in champion_requirements.values()) and all(
        detail["satisfied"] for detail in trait_requirements.values()
    )
    if tank_requirement:
        all_satisfied = all_satisfied and tank_requirement["satisfied"]

    return {
        "champions": champion_requirements,
        "traits": trait_requirements,
        "tank": tank_requirement,
        "all_satisfied": all_satisfied,
    }


def run_bfl(config: Config) -> Dict[str, object]:
    """Execute the Bronze for Life solver and return a structured result."""

    decision_log: List[str] = []
    decision_log.append(f"config: {json.dumps(config.to_dict(), sort_keys=True)}")

    context_details: Dict[str, object] = {"config": config.to_dict()}

    try:
        set_data, champs, champ_traits, trait_bps, champ_cost, eligible_traits, trait_freq = (
            load_set_data(config.json_path, config.set_id, config.blacklist_traits_by_name)
        )

        validate_config_against_data(config, champs, trait_bps)

        metatft_text = load_metatft_txt(str(config.metatft_txt_path))
        unit_stats = metatft_to_unit_stats(metatft_text, set_data)
        tank_champions = classify_tank_champions(unit_stats, champ_cost)
        tank_champion_filter = tank_champions if config.must_have_itemized_tank else None

        if config.must_have_itemized_tank and not tank_champions:
            raise RuntimeError(
                "Must-have tank requirement enabled, but no tank champions could be identified from MetaTFT data."
            )

        trait_text = load_metatft_txt(str(config.metatft_traits_path))
        trait_stats = metatft_to_trait_stats(trait_text, set_data)

        power_map = {
            c: unit_power(c, unit_stats, config.w_win, config.w_avg, config.w_freq) for c in champs
        }

        if len(champs) < config.team_size:
            raise RuntimeError(
                f"Not enough playable units after filtering: {len(champs)} (need {config.team_size})."
            )

        ryze_region_traits = None
        if config.mode == "ryze":
            ryze_region_traits = region_trait_pool(trait_bps)
            eligible_traits = ryze_region_traits

        context_payload: Dict[str, object] = {
            "champion_count": len(champs),
            "trait_breakpoint_count": len(trait_bps),
            "blacklist_traits": sorted(config.blacklist_traits_by_name),
            "eligible_traits": sorted(eligible_traits),
            "emblem_start_counts": config.emblem_start_counts,
            "max_emblems_total": config.max_emblems_total,
            "mode": config.mode,
            "seed_verticals": config.seed_verticals,
            "must_have_itemized_tank": config.must_have_itemized_tank,
            "tank_candidates": sorted(tank_champions),
        }
        if ryze_region_traits is not None:
            context_payload["region_traits"] = sorted(ryze_region_traits)

        context_details.update(context_payload)

        (
            team,
            emblem_counts,
            team_power,
            bronze_count,
            counts,
            bronze_traits,
            active_traits,
            upgraded_traits,
            used_traits,
        ) = solve_beam_search_bronze_with_emblems(
            champs,
            champ_traits,
            trait_bps,
            eligible_traits,
            config.team_size,
            config.beam_width,
            config.emblem_start_counts,
            config.max_emblems_total,
            power_map,
            required_champions={k: v for k, v in config.required_champions.items() if v != 0},
            required_traits_min=config.required_traits_min,
            trait_stats=trait_stats if config.mode == "standard" else None,
            tank_champions=tank_champion_filter,
            mode=config.mode,
            trait_weights=(config.w_win, config.w_avg, config.w_freq),
            champ_slot_sizes=SPECIAL_CHAMPION_SLOT_SIZES,
            trait_value_overrides=SPECIAL_TRAIT_VALUE_OVERRIDES,
            must_include_one_of=tank_champion_filter if config.must_have_itemized_tank else None,
            seed_verticals=config.seed_verticals,
            decision_log=decision_log,
        )
    except Exception as exc:
        decision_log.append(f"error: {exc}")
        raise SolverError(str(exc), decision_log, context_details) from exc

    trait_metatft: Dict[str, Dict[str, object]] = {}
    if trait_stats:
        for trait, count in counts.items():
            stat = best_trait_stat(trait, count, trait_stats)
            if not stat:
                continue
            trait_metatft[trait] = {
                "required": stat.required,
                "tier": stat.tier,
                "avg": stat.avg,
                "win": stat.win,
                "freq": stat.freq,
            }

    requirements = _build_requirement_details(team, counts, config, tank_champions)

    context_details.update(
        {
            "set_id": config.set_id,
            "json_path": str(config.json_path),
            "team_size": config.team_size,
            "beam_width": config.beam_width,
            "trait_breakpoints": trait_bps,
            "trait_frequency": trait_freq,
        }
    )

    return {
        "context": context_details,
        "meta": {
            "enabled": bool(unit_stats),
            "weights": {"w_win": config.w_win, "w_avg": config.w_avg, "w_freq": config.w_freq},
            "unit_stats": unit_stats,
            "trait_stats_enabled": bool(trait_stats),
        },
        "solution": {
            "team": sorted(team),
            "emblems": emblem_counts,
            "team_power": team_power,
            "bronze_count": bronze_count,
            "trait_counts": counts,
            "bronze_traits": bronze_traits,
            "active_traits": active_traits,
            "upgraded_traits": upgraded_traits,
            "used_traits": used_traits,
            "trait_metatft": trait_metatft,
        },
        "units": {
            c: {
                "traits": champ_traits[c],
                "cost": champ_cost.get(c),
                "metatft": unit_stats.get(c) if unit_stats else None,
            }
            for c in team
        },
        "requirements": requirements,
        "debug_log": decision_log,
    }


def run_solver(config: Config) -> Dict[str, object]:
    """Execute the requested solver mode and return a structured result."""

    if config.mode == "itemization":
        try:
            return run_itemization_solver(config)
        except ItemizationError as exc:
            raise SolverError(str(exc), exc.debug_log, exc.context) from exc

    return run_bfl(config)
