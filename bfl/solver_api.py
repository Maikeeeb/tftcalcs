"""Structured API for running Bronze for Life solver."""

from pathlib import Path
from typing import Dict, List, Set

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
    "solve_beam_search_bronze_with_emblems",
    "unit_power",
    "trait_power",
    "apply_emblem_starts",
    "classify_traits",
    "run_bfl",
]

BARON_API_NAME = "TFT16_BaronNashor"

SPECIAL_CHAMPION_SLOT_SIZES = {BARON_API_NAME: 2}
SPECIAL_TRAIT_VALUE_OVERRIDES = {BARON_API_NAME: {"Void": 2}}


def _resolve_config(config: Config | None, config_path: str | None) -> Config:
    if config is not None:
        return config

    default_path = Path(config_path) if config_path else REPO_ROOT / DEFAULT_CONFIG_FILENAME
    if config_path or default_path.exists():
        return load_config(str(default_path))

    return load_config(None)


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

    set_data, champs, champ_traits, trait_bps, champ_cost, eligible_traits, trait_freq = load_set_data(
        config.json_path, config.set_id, config.blacklist_traits_by_name
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

    power_map = {c: unit_power(c, unit_stats, config.w_win, config.w_avg, config.w_freq) for c in champs}

    if len(champs) < config.team_size:
        raise RuntimeError(
            f"Not enough playable units after filtering: {len(champs)} (need {config.team_size})."
        )

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
    )

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

    return {
        "context": {
            "set_id": config.set_id,
            "json_path": str(config.json_path),
            "team_size": config.team_size,
            "beam_width": config.beam_width,
            "blacklist_traits": sorted(config.blacklist_traits_by_name),
            "eligible_traits": sorted(eligible_traits),
            "trait_breakpoints": trait_bps,
            "trait_frequency": trait_freq,
            "champion_count": len(champs),
            "trait_breakpoint_count": len(trait_bps),
            "emblem_start_counts": config.emblem_start_counts,
            "max_emblems_total": config.max_emblems_total,
            "mode": config.mode,
            "seed_verticals": config.seed_verticals,
        },
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
    }

