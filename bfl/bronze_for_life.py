from bfl.config import Config
from bfl.solver_api import (
    apply_emblem_starts,
    build_name_to_api_map,
    classify_traits,
    load_metatft_txt,
    load_set_data,
    metatft_to_unit_stats,
    normalize_name,
    parse_metatft_units,
    run_bfl,
    solve_beam_search_bronze_with_emblems,
    unit_power,
    _resolve_config,
)

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


def main(config: Config | None = None, config_path: str | None = None):
    cfg = _resolve_config(config, config_path)
    result = run_bfl(cfg)

    context = result["context"]
    meta = result["meta"]
    solution = result["solution"]
    units = result["units"]

    trait_bps = context["trait_breakpoints"]
    trait_freq = context["trait_frequency"]
    eligible_traits = set(context["eligible_traits"])

    print(f"Loaded set {context['set_id']}: {context['champion_count']} real units after filtering")
    print(f"Traits with breakpoints: {context['trait_breakpoint_count']}")
    print(f"Blacklisted traits (never count): {context['blacklist_traits']}")
    print(f"Eligible traits for Bronze for Life: {len(context['eligible_traits'])}")
    print(f"TEAM_SIZE={context['team_size']}")
    print(f"Hard emblems: {context['emblem_start_counts']}")
    print(f"Auto-emblems allowed (total): {context['max_emblems_total']}")

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
    if meta["enabled"]:
        print(
            f"MetaTFT weighting enabled: W_WIN={cfg.w_win}, W_AVG={cfg.w_avg}, W_FREQ={cfg.w_freq}"
        )
    else:
        print("MetaTFT weighting disabled (METATFT_PASTE is empty).")
    print("Optimizing for MAX bronze-active eligible traits...\n")

    team = solution["team"]
    emblem_counts = solution["emblems"]
    counts = solution["trait_counts"]
    bronze_traits = solution["bronze_traits"]
    upgraded_traits = solution["upgraded_traits"]
    used_traits = solution["used_traits"]

    print("=== Result (Bronze for Life + Emblems + Unit Strength) ===")
    print(f"Bronze-active eligible trait count: {solution['bronze_count']}")
    if emblem_counts:
        print(f"Emblem starting counts used: {emblem_counts}")
    if meta["enabled"]:
        print(f"Team power (MetaTFT tie-break): {solution['team_power']:.4f}")
    print()

    print("Team (unit -> traits):")
    for c in sorted(team):
        extra = ""
        stats = units.get(c, {}).get("metatft") if meta["enabled"] else None
        if stats:
            extra = f" | avg={stats['avg']:.2f} win={stats['win'] * 100:.1f}% freq={stats['freq'] * 100:.1f}%"
        traits = units.get(c, {}).get("traits")
        cost = units.get(c, {}).get("cost")
        print(f" - {c} (cost={cost}) -> {traits}{extra}")

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
