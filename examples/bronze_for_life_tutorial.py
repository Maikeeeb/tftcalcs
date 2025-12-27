"""Walk-through examples for building Bronze for Life teams.

Run this module directly to see common configurations:
- No emblems
- A couple of fixed emblems
- Automatic emblem selection
- Forced units
"""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from bfl.bronze_for_life import (
    load_metatft_txt,
    load_set_data,
    metatft_to_unit_stats,
    solve_beam_search_bronze_with_emblems,
    unit_power,
)
from bfl.config_loader import load_config

CONFIG = load_config(None)

# Keep tutorial runs snappy even if the config beam is large.
BEAM_WIDTH_EXAMPLE = min(CONFIG.beam_width, 100)


def prepare_context():
    """Load set data and pre-compute power map once for all examples."""
    (
        set_data,
        champs,
        champ_traits,
        trait_bps,
        champ_cost,
        eligible_traits,
        _trait_freq,
    ) = load_set_data(CONFIG.json_path, CONFIG.set_id, CONFIG.blacklist_traits_by_name)

    metatft_text = load_metatft_txt(str(CONFIG.metatft_txt_path))
    unit_stats = metatft_to_unit_stats(metatft_text, set_data)
    power_map = {c: unit_power(c, unit_stats, CONFIG.w_win, CONFIG.w_avg, CONFIG.w_freq) for c in champs}

    return {
        "champs": champs,
        "champ_traits": champ_traits,
        "trait_bps": trait_bps,
        "eligible_traits": eligible_traits,
        "power_map": power_map,
        "champ_cost": champ_cost,
    }


def run_case(title, hard_emblems, max_auto_emblems, ctx, forced_units=None):
    result = solve_beam_search_bronze_with_emblems(
        ctx["champs"],
        ctx["champ_traits"],
        ctx["trait_bps"],
        ctx["eligible_traits"],
        CONFIG.team_size,
        BEAM_WIDTH_EXAMPLE,
        hard_emblems,
        max_auto_emblems,
        ctx["power_map"],
        forced_units=forced_units,
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
        _used_traits,
    ) = result

    print(f"\n=== {title} ===")
    print(f"Bronze-eligible traits at tier 1: {bronze_count}")
    print(f"Active eligible traits (any tier): {len(active_traits)}")
    if BEAM_WIDTH_EXAMPLE != CONFIG.beam_width:
        print(f"Beam width (example override): {BEAM_WIDTH_EXAMPLE} (config={CONFIG.beam_width})")
    if emblem_counts:
        print(f"Emblems applied: {emblem_counts}")
    if team_power:
        print(f"MetaTFT tie-break power: {team_power:.4f}")
    if forced_units:
        print(f"Forced units locked in: {forced_units}")

    print("Team:")
    for c in sorted(team):
        traits = ", ".join(ctx["champ_traits"][c])
        print(f" - {c} (cost {ctx['champ_cost'].get(c)}) -> {traits}")

    print("Bronze traits:")
    for t in sorted(bronze_traits):
        print(f" - {t}: {counts.get(t, 0)}")

    if upgraded_traits:
        print("Upgraded traits (tier 2+):")
        for t in sorted(upgraded_traits):
            print(f" - {t}: {counts.get(t, 0)}")


def main():
    ctx = prepare_context()

    # 1) No emblems
    run_case("No emblems", hard_emblems={}, max_auto_emblems=0, ctx=ctx)

    # 2) Two fixed emblems applied up front
    run_case(
        "Two fixed emblems (Zaun + Vanquisher)",
        hard_emblems={"Zaun": 1, "Vanquisher": 1},
        max_auto_emblems=0,
        ctx=ctx,
    )

    # 3) Let the solver auto-select up to two emblems
    run_case(
        "Auto-select up to two emblems",
        hard_emblems={},
        max_auto_emblems=2,
        ctx=ctx,
    )

    # 4) Pin core carries but let the rest float
    run_case(
        "Forced units (Tristana + Lulu locked)",
        hard_emblems={},
        max_auto_emblems=1,
        ctx=ctx,
        forced_units=("TFT16_Tristana", "TFT16_Lulu"),
    )


if __name__ == "__main__":
    main()
