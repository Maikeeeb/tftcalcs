from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Set, Tuple

from bfl.traits import apply_emblem_starts, classify_traits


def compute_effective_counts(base_counts: Dict[str, int], emblem_counts: Dict[str, int]) -> Dict[str, int]:
    """Return counts after applying emblem starts."""

    return apply_emblem_starts(base_counts, emblem_counts)


def requirement_gap(required_traits_min: Dict[str, int], counts: Dict[str, int]) -> int:
    """How many total trait stacks are still missing to satisfy requirements."""

    if not required_traits_min:
        return 0

    return sum(max(0, need - counts.get(t, 0)) for t, need in required_traits_min.items() if need > 0)


def build_required_team(
    champs: List[str],
    champ_traits: Dict[str, List[str]],
    power_map: Dict[str, float],
    required_champions: Optional[Dict[str, int]],
    forced_units: Optional[Iterable[str]] = None,
    team_size: Optional[int] = None,
) -> Tuple[List[str], Dict[str, int], float]:
    """Assemble the starting team from forced and required champions."""

    required_map = required_champions or {}
    champs_set = set(champs)

    start_team: List[str] = []

    def _add_candidate(candidate: str):
        if candidate not in champs_set:
            raise RuntimeError(
                f"Required champion '{candidate}' is not in the playable pool; check name or filtering."
            )
        if candidate not in start_team:
            start_team.append(candidate)

    for c, flag in required_map.items():
        if flag not in (0, 1):
            raise RuntimeError(f"Required champion '{c}' must be 0 or 1, got {flag}.")
        if flag:
            _add_candidate(c)

    if forced_units:
        for c in forced_units:
            _add_candidate(c)

    if team_size is not None and len(start_team) > team_size:
        raise RuntimeError(
            f"Required champions count ({len(start_team)}) exceeds TEAM_SIZE={team_size}."
        )

    base_counts = defaultdict(int)
    team_power = 0.0
    for c in start_team:
        for t in champ_traits[c]:
            base_counts[t] += 1
        team_power += power_map.get(c, 0.0)

    return start_team, base_counts, team_power


def feasibility_check(
    base_counts: Dict[str, int],
    choose_best_emblems,
    required_traits_min: Dict[str, int],
    remaining_slots: int,
) -> bool:
    if not required_traits_min:
        return True

    emblem_counts = choose_best_emblems(base_counts)
    effective = compute_effective_counts(base_counts, emblem_counts)

    for t, need_min in required_traits_min.items():
        if need_min <= 0:
            continue
        need = need_min - effective.get(t, 0)
        if need > remaining_slots:
            return False
    return True


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
    required_champions: Optional[Dict[str, int]] = None,
    required_traits_min: Optional[Dict[str, int]] = None,
    forced_units: Optional[Iterable[str]] = None,
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

    required_traits_min = required_traits_min or {}

    # Validate required traits
    for t, min_count in required_traits_min.items():
        if min_count < 0:
            raise RuntimeError(f"Required trait '{t}' minimum cannot be negative (got {min_count}).")
        if min_count > 0 and t not in trait_bps:
            raise RuntimeError(
                f"Required trait '{t}' is not in the trait list (trait_bps). Check spelling or set data."
            )

    start_team, base_counts0, team_power0 = build_required_team(
        champs, champ_traits, power_map, required_champions, forced_units, team_size
    )

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

    def score_state(base_counts: Dict[str, int]) -> Tuple[int, int, int, int, Dict[str, int]]:
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

        missing_requirements = requirement_gap(required_traits_min, cnt2)

        return bronze, active, upgraded, missing_requirements, emblem_counts

    # ----------------------------
    # Beam search starting from forced/required team
    # ----------------------------
    # Beam state: (team, base_counts, team_power, sort_key)
    bronze0, active0, upgraded0, missing0, _ = score_state(base_counts0)
    beam: List[Tuple[List[str], Dict[str, int], float, Tuple[int, int, int, int, float]]] = []

    remaining_slots0 = team_size - len(start_team)
    if feasibility_check(base_counts0, choose_best_emblems, required_traits_min, remaining_slots0):
        beam.append(
            (
                start_team,
                base_counts0,
                team_power0,
                (-missing0, bronze0, active0, -upgraded0, team_power0),
            )
        )

    for _ in range(remaining_slots0):
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

                new_power = team_power + power_map.get(c, 0.0)
                new_remaining_slots = team_size - len(new_team)

                if not feasibility_check(
                    new_counts, choose_best_emblems, required_traits_min, new_remaining_slots
                ):
                    continue

                bronze, active, upgraded, missing, _ = score_state(new_counts)

                key = (-missing, bronze, active, -upgraded, new_power)
                candidates.append((new_team, new_counts, new_power, key))

        candidates.sort(key=lambda x: x[3], reverse=True)
        beam = candidates[:beam_width]

        if not beam:
            break

    if not beam:
        raise RuntimeError(
            "Beam search produced no candidates under the given constraints. Check filtering/requirements."
        )

    best_team, best_base_counts, best_power, _best_key = max(beam, key=lambda x: x[3])

    emblem_counts = choose_best_emblems(best_base_counts)

    counts, bronze_traits, active_traits, upgraded_traits, used_traits = classify_traits(
        best_team, champ_traits, trait_bps, eligible_traits, emblem_counts
    )

    for t, min_count in required_traits_min.items():
        if min_count <= 0:
            continue
        if counts.get(t, 0) < min_count:
            raise RuntimeError(
                f"No team satisfies required trait minimums; '{t}' needed {min_count}, got {counts.get(t, 0)}."
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
