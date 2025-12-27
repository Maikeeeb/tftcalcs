from bfl.config import (
    BEAM_WIDTH,
    BLACKLIST_TRAITS_BY_NAME,
    EMBLEM_START_COUNTS,
    JSON_PATH,
    MAX_EMBLEMS_TOTAL,
    METATFT_TXT_PATH,
    REQUIRED_CHAMPIONS,
    REQUIRED_TRAITS_MIN,
    SET_ID,
    TEAM_SIZE,
    W_AVG,
    W_FREQ,
    W_WIN,
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


def main():
    set_data, champs, champ_traits, trait_bps, champ_cost, eligible_traits, trait_freq = load_set_data(
        JSON_PATH, SET_ID
    )

    def build_template(keys, provided):
        template = {k: 0 for k in keys}
        if not provided:
            return template

        invalid = [k for k, v in provided.items() if v > 0 and k not in template]
        if invalid:
            raise RuntimeError(
                f"Invalid required keys (not in data): {sorted(invalid)}. Update config or set to 0."
            )

        template.update({k: provided[k] for k in provided if k in template})
        return template

    required_champions = build_template(champs, REQUIRED_CHAMPIONS)
    required_traits_min = build_template(trait_bps, REQUIRED_TRAITS_MIN)

    # Load MetaTFT stats (optional)
    metatft_text = load_metatft_txt(str(METATFT_TXT_PATH))
    unit_stats = metatft_to_unit_stats(metatft_text, set_data)

    # Precompute unit power for beam search
    power_map = {c: unit_power(c, unit_stats) for c in champs}

    print(f"Loaded set {SET_ID}: {len(champs)} real units after filtering")
    print(f"Traits with breakpoints: {len(trait_bps)}")
    print(f"Blacklisted traits (never count): {sorted(BLACKLIST_TRAITS_BY_NAME)}")
    print(f"Eligible traits for Bronze for Life: {len(eligible_traits)}")
    print(f"TEAM_SIZE={TEAM_SIZE}")
    print(f"Hard emblems: {EMBLEM_START_COUNTS}")
    print(f"Auto-emblems allowed (total): {MAX_EMBLEMS_TOTAL}")
    enabled_champs = [c for c, v in required_champions.items() if v > 0]
    enabled_traits = {t: v for t, v in required_traits_min.items() if v > 0}
    if enabled_champs or enabled_traits:
        print("Constraints enabled:")
        if enabled_champs:
            print(f" - Required champions: {enabled_champs}")
        if enabled_traits:
            print(f" - Required trait minimums: {enabled_traits}")
    if unit_stats:
        print(f"MetaTFT weighting enabled: W_WIN={W_WIN}, W_AVG={W_AVG}, W_FREQ={W_FREQ}")
    else:
        print("MetaTFT weighting disabled (METATFT_PASTE is empty).")
    print("Optimizing for MAX bronze-active eligible traits...\n")

    if len(champs) < TEAM_SIZE:
        raise RuntimeError(f"Not enough playable units after filtering: {len(champs)} (need {TEAM_SIZE}).")

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
        TEAM_SIZE,
        BEAM_WIDTH,
        EMBLEM_START_COUNTS,
        MAX_EMBLEMS_TOTAL,
        power_map,
        required_champions=required_champions,
        required_traits_min=required_traits_min,
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
            if t in BLACKLIST_TRAITS_BY_NAME:
                reason.append("blacklisted")
            if trait_freq.get(t, 0) < 2:
                reason.append("exclusive")
            print(f" - {t}: teamCount={counts.get(t, 0)} traitFreq={trait_freq.get(t)} ({', '.join(reason)})")


if __name__ == "__main__":
    main()
