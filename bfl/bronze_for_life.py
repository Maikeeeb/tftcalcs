from pathlib import Path

from bfl.config import Config, REPO_ROOT
from bfl.config_loader import (
    DEFAULT_CONFIG_FILENAME,
    load_config,
    validate_config_against_data,
)
from bfl.metatft import (
    build_name_to_api_map,
    load_metatft_txt,
    metatft_to_unit_stats,
    normalize_name,
    parse_metatft_units,
    unit_power,
)
from bfl.set_loader import load_set_data
from bfl.solver import solve_beam_search_bronze_with_emblems
from bfl.traits import apply_emblem_starts, classify_traits

__all__ = [
    "apply_emblem_starts",
    "build_name_to_api_map",
    "classify_traits",
    "load_set_data",
    "load_metatft_txt",
    "metatft_to_unit_stats",
    "normalize_name",
    "parse_metatft_units",
    "solve_beam_search_bronze_with_emblems",
    "unit_power",
]


def _resolve_config(config: Config | None, config_path: str | None) -> Config:
    if config is not None:
        return config

    default_path = Path(config_path) if config_path else REPO_ROOT / DEFAULT_CONFIG_FILENAME
    if config_path or default_path.exists():
        return load_config(str(default_path))

    return load_config(None)


def main(config: Config | None = None, config_path: str | None = None):
    cfg = _resolve_config(config, config_path)

    set_data, champs, champ_traits, trait_bps, champ_cost, eligible_traits, trait_freq = load_set_data(
        cfg.json_path, cfg.set_id, cfg.blacklist_traits_by_name
    )

    validate_config_against_data(cfg, champs, trait_bps)

    # Load MetaTFT stats (optional)
    metatft_text = load_metatft_txt(str(cfg.metatft_txt_path))
    unit_stats = metatft_to_unit_stats(metatft_text, set_data)

    # Precompute unit power for beam search
    power_map = {c: unit_power(c, unit_stats, cfg.w_win, cfg.w_avg, cfg.w_freq) for c in champs}

    print(f"Loaded set {cfg.set_id}: {len(champs)} real units after filtering")
    print(f"Traits with breakpoints: {len(trait_bps)}")
    print(f"Blacklisted traits (never count): {sorted(cfg.blacklist_traits_by_name)}")
    print(f"Eligible traits for Bronze for Life: {len(eligible_traits)}")
    print(f"TEAM_SIZE={cfg.team_size}")
    print(f"Hard emblems: {cfg.emblem_start_counts}")
    print(f"Auto-emblems allowed (total): {cfg.max_emblems_total}")

    enabled_champs = [c for c, v in cfg.required_champions.items() if v > 0]
    disabled_champs = [c for c, v in cfg.required_champions.items() if v < 0]
    enabled_traits = {t: v for t, v in cfg.required_traits_min.items() if v > 0}
    if enabled_champs or enabled_traits:
        print("Constraints enabled:")
        if enabled_champs:
            print(f" - Required champions: {enabled_champs}")
        if disabled_champs:
            print(f" - Banned champions: {disabled_champs}")
        if enabled_traits:
            print(f" - Required trait minimums: {enabled_traits}")
    if unit_stats:
        print(f"MetaTFT weighting enabled: W_WIN={cfg.w_win}, W_AVG={cfg.w_avg}, W_FREQ={cfg.w_freq}")
    else:
        print("MetaTFT weighting disabled (METATFT_PASTE is empty).")
    print("Optimizing for MAX bronze-active eligible traits...\n")

    if len(champs) < cfg.team_size:
        raise RuntimeError(f"Not enough playable units after filtering: {len(champs)} (need {cfg.team_size}).")

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
        cfg.team_size,
        cfg.beam_width,
        cfg.emblem_start_counts,
        cfg.max_emblems_total,
        power_map,
        required_champions={k: v for k, v in cfg.required_champions.items() if v != 0},
        required_traits_min=cfg.required_traits_min,
    )

    print("=== Result (Bronze for Life + Emblems + Unit Strength) ===")
    print(f"Bronze-active eligible trait count: {bronze_count}")
    if emblem_counts:
        print(f"Emblem starting counts used: {emblem_counts}")
    if unit_stats:
        print(f"Team power (MetaTFT tie-break): {team_power:.4f}")
    print()

    print("Team (unit -> traits):")
    for c in sorted(team):
        extra = ""
        if unit_stats and c in unit_stats:
            s = unit_stats[c]
            extra = f" | avg={s['avg']:.2f} win={s['win'] * 100:.1f}% freq={s['freq'] * 100:.1f}%"
        print(f" - {c} (cost={champ_cost.get(c)}) -> {champ_traits[c]}{extra}")

    print("\nBronze-active eligible traits (tier 1 only, after emblems):")
    for t in bronze_traits:
        bps = trait_bps[t]
        c = counts.get(t, 0)
        if len(bps) >= 2:
            print(f" - {t}: {c} (range {bps[0]} to {bps[1] - 1})")
        else:
            print(f" - {t}: {c} (min {bps[0]})")

    print("\nUpgraded eligible traits (hit tier 2+; NOT bronze):")
    if not upgraded_traits:
        print(" - (none)")
    else:
        for t in upgraded_traits:
            bps = trait_bps[t]
            print(f" - {t}: {counts.get(t, 0)} (tier2 at {bps[1]})")

    # Optional debug: show ineligible traits present on team (exclusive or blacklisted)
    ineligible_present = [t for t in used_traits if t in trait_bps and t not in eligible_traits]
    if ineligible_present:
        print("\nIneligible traits present on team (do NOT count):")
        for t in sorted(ineligible_present):
            reason = []
            if t in cfg.blacklist_traits_by_name:
                reason.append("blacklisted")
            if trait_freq.get(t, 0) < 2:
                reason.append("exclusive")
            print(f" - {t}: teamCount={counts.get(t, 0)} traitFreq={trait_freq.get(t)} ({', '.join(reason)})")


if __name__ == "__main__":
    main()
