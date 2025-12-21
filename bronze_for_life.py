import json
import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple

JSON_PATH = "en_us.json"
SET_ID = "16"
METATFT_TXT_PATH = "metatft_units.txt"

TEAM_SIZE = 9
BEAM_WIDTH = 700  # bigger = better results, slower

# Traits that should NEVER count for Bronze for Life even if active.
BLACKLIST_TRAITS_BY_NAME: Set[str] = {
    "Targon",
}

# --- Emblem modeling (simple) ---
# If a trait is in EMBLEM_START_COUNTS, it starts at that many units (e.g., 1 emblem => +1).
EMBLEM_START_COUNTS: Dict[str, int] = {
    "Zaun": 1,
    "Ixtal": 1,
    "Freljord": 1,
    "Bilgewater": 1,
}

# If > 0, the optimizer will choose up to this many traits to receive +1 starting count (emblem),
# unless you hard-code EMBLEM_START_COUNTS above (hard-coded counts are always applied).
MAX_EMBLEMS_TOTAL = 0  # set 0 to disable automatic emblem selection

# Weights for unit strength tie-breaker.
# Higher = optimizer prefers "stronger" units among equally good bronze solutions.
W_WIN = 2.0  # win rate (0..1)
W_AVG = 1.0  # avg placement (lower is better)
W_FREQ = 0.1  # optional: popularity stability (0..1). keep small.


def load_metatft_txt(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"MetaTFT file not found: {path}")
        return ""













def main():
    set_data, champs, champ_traits, trait_bps, champ_cost, eligible_traits, trait_freq = load_set_data(JSON_PATH,
                                                                                                       SET_ID)

    # Load MetaTFT stats (optional)
    metatft_text = load_metatft_txt(METATFT_TXT_PATH)
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
    if unit_stats:
        print(f"MetaTFT weighting enabled: W_WIN={W_WIN}, W_AVG={W_AVG}, W_FREQ={W_FREQ}")
    else:
        print("MetaTFT weighting disabled (METATFT_PASTE is empty).")
    print("Optimizing for MAX bronze-active eligible traits...\n")

    if len(champs) < TEAM_SIZE:
        raise RuntimeError(f"Not enough playable units after filtering: {len(champs)} (need {TEAM_SIZE}).")

    team, emblem_counts, team_power, bronze_count, counts, bronze_traits, active_traits, upgraded_traits, used_traits = (
        solve_beam_search_bronze_with_emblems(
            champs, champ_traits, trait_bps, eligible_traits,
            TEAM_SIZE, BEAM_WIDTH,
            EMBLEM_START_COUNTS, MAX_EMBLEMS_TOTAL,
            power_map
        )
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
