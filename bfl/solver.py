from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional, Iterable

from bfl.traits import apply_emblem_starts, classify_traits


def solve_beam_search_bronze_with_emblems(
    champs: List[str],
    champ_traits: Dict[str, List[str]],
    trait_bps: Dict[str, List[int]],
    eligible_traits: Set[str],
    team_size: int,
    beam_width: int,
    hard_emblems: Dict[str, int],
    max_emblems_total: int,
    power_map: Dict[str, float],
    forced_units: Optional[Iterable[str]] = None,   # <-- NEW
):
    """
    Beam search for max bronze-active traits, with emblems.
    Tie-breakers (in this order):
      1) bronze count (eligible, tier1-only)
      2) active eligible traits (any tier)
      3) fewer upgraded (tier2+)
      4) higher team power (from MetaTFT)

    forced_units:
      Optional iterable of champion apiNames that MUST be included in the final team.
      Example: ["TFT16_Alpha", "TFT16_Beta"]
    """

    # ----------------------------
    # Validate and normalize forced units
    # ----------------------------
    forced_list: List[str] = []
    if forced_units:
        forced_list = list(forced_units)

    # Remove duplicates while preserving order
    seen = set()
    forced_list_unique = []
    for u in forced_list:
        if u not in seen:
            seen.add(u)
            forced_list_unique.append(u)
    forced_list = forced_list_unique

    if len(forced_list) > team_size:
        raise ValueError(
            f"forced_units has {len(forced_list)} units but team_size={team_size}. "
            f"Forced units must be <= team size."
        )

    champs_set = set(champs)
    missing = [u for u in forced_list if u not in champs_set]
    if missing:
        raise ValueError(
            f"Some forced_units are not in champs (filtered playable list): {missing}. "
            f"Either they were filtered out (cost/traits) or the apiName is wrong."
        )

    # Build initial partial team + counts from forced units
    base_counts0 = defaultdict(int)
    team_power0 = 0.0
    for c in forced_list:
        for t in champ_traits[c]:
            base_counts0[t] += 1
        team_power0 += power_map.get(c, 0.0)

    start_team = list(forced_list)

    # ----------------------------
    # Emblem helpers (unchanged)
    # ----------------------------
    auto_candidates = sorted([t for t in eligible_traits if t not in hard_emblems])

    def choose_best_emblems(base_counts: Dict[str, int]) -> Dict[str, int]:
        if max_emblems_total <= 0:
            return dict(hard_emblems)

        chosen = dict(hard_emblems)

        def eval_with(chosen_emblems: Dict[str, int]) -> Tuple[int, int, int]:
            cnt2 = apply_emblem_starts(base_counts, chosen_emblems)
            bronze = 0
            active = 0
            upgraded = 0
            for t in eligible_traits:
                bps = trait_bps[t]
                c = cnt2.get(t, 0)
                if c < bps[0]:
                    continue
                active += 1
                if len(bps) == 1:
                    bronze += 1
                else:
                    if c < bps[1]:
                        bronze += 1
                    else:
                        upgraded += 1
            return bronze, active, upgraded

        already_used = sum(chosen.values())
        remaining = max(0, max_emblems_total - already_used)
        if remaining == 0:
            return chosen

        for _ in range(remaining):
            best_t = None
            best_key = None

            for t in auto_candidates:
                if t in chosen:
                    continue

                trial = dict(chosen)
                trial[t] = 1
                bronze, active, upgraded = eval_with(trial)
                key = (bronze, active, -upgraded)

                if best_key is None or key > best_key:
                    best_key = key
                    best_t = t

            if best_t is None:
                break
            chosen[best_t] = 1

        return chosen

    def score_state(base_counts: Dict[str, int]) -> Tuple[int, int, int, Dict[str, int]]:
        emblem_counts = choose_best_emblems(base_counts)
        cnt2 = apply_emblem_starts(base_counts, emblem_counts)

        bronze = 0
        active = 0
        upgraded = 0

        for t in eligible_traits:
            bps = trait_bps[t]
            c = cnt2.get(t, 0)
            if c < bps[0]:
                continue
            active += 1
            if len(bps) == 1:
                bronze += 1
            else:
                if c < bps[1]:
                    bronze += 1
                else:
                    upgraded += 1

        return bronze, active, upgraded, emblem_counts

    # ----------------------------
    # Beam search starting from forced team
    # ----------------------------
    # Beam state: (team, base_counts, team_power, sort_key)
    bronze0, active0, upgraded0, _ = score_state(base_counts0)
    beam: List[Tuple[List[str], Dict[str, int], float, Tuple[int, int, int, float]]] = [
        (start_team, base_counts0, team_power0, (bronze0, active0, -upgraded0, team_power0))
    ]

    remaining_slots = team_size - len(start_team)

    for _ in range(remaining_slots):
        candidates = []
        for team, base_counts, team_power, _key in beam:
            team_set = set(team)
            for c in champs:
                if c in team_set:
                    continue

                new_team = team + [c]
                new_counts = defaultdict(int, base_counts)
                for t in champ_traits[c]:
                    new_counts[t] += 1

                bronze, active, upgraded, _ = score_state(new_counts)
                new_power = team_power + power_map.get(c, 0.0)

                key = (bronze, active, -upgraded, new_power)
                candidates.append((new_team, new_counts, new_power, key))

        candidates.sort(key=lambda x: x[3], reverse=True)
        beam = candidates[:beam_width]

        if not beam:
            break

    if not beam:
        raise RuntimeError("Beam search produced no candidates. Check filtering logic.")

    best_team, best_base_counts, best_power, _best_key = max(beam, key=lambda x: x[3])

    emblem_counts = choose_best_emblems(best_base_counts)

    counts, bronze_traits, active_traits, upgraded_traits, used_traits = classify_traits(
        best_team, champ_traits, trait_bps, eligible_traits, emblem_counts
    )

    return (
        best_team,
        emblem_counts,
        best_power,
        len(bronze_traits),
        counts,
        bronze_traits,
        active_traits,
        upgraded_traits,
        used_traits,
    )
