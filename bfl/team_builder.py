"""Team assembly and validation functions."""

from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Set, Tuple

from bfl.traits import add_champion_traits, apply_emblem_starts


def _team_slots(team: List[str], champ_slot_sizes: Dict[str, int]) -> int:
    return sum(champ_slot_sizes.get(c, 1) for c in team)


def compute_effective_counts(
    base_counts: Dict[str, int], emblem_counts: Dict[str, int]
) -> Dict[str, int]:
    """Return counts after applying emblem starts."""

    return apply_emblem_starts(base_counts, emblem_counts)


def requirement_gap(required_traits_min: Dict[str, int], counts: Dict[str, int]) -> int:
    """How many total trait stacks are still missing to satisfy requirements."""

    if not required_traits_min:
        return 0

    return sum(
        max(0, need - counts.get(t, 0)) for t, need in required_traits_min.items() if need > 0
    )


def build_required_team(
    champs: List[str],
    champ_traits: Dict[str, List[str]],
    power_map: Dict[str, float],
    required_champions: Optional[Dict[str, int]],
    champ_slot_sizes: Optional[Dict[str, int]] = None,
    trait_value_overrides: Optional[Dict[str, Dict[str, int]]] = None,
    forced_units: Optional[Iterable[str]] = None,
    team_size: Optional[int] = None,
) -> Tuple[List[str], Dict[str, int], float]:
    """Assemble the starting team from forced and required champions."""

    required_map = required_champions or {}
    slot_sizes = champ_slot_sizes or {}
    champs_set = set(champs)

    start_team: List[str] = []

    def _validate_candidate(candidate: str):
        if candidate not in champs_set:
            raise RuntimeError(
                f"Required champion '{candidate}' is not in the playable pool; check name or filtering."
            )

    def _add_candidate(candidate: str):
        _validate_candidate(candidate)
        if candidate not in start_team:
            start_team.append(candidate)

    for c, flag in required_map.items():
        if flag not in (-1, 0, 1):
            raise RuntimeError(f"Required champion '{c}' must be -1, 0 or 1, got {flag}.")
        _validate_candidate(c)
        if flag < 0:
            continue
        if flag:
            _add_candidate(c)

    if forced_units:
        for c in forced_units:
            _add_candidate(c)

    starting_slots = _team_slots(start_team, slot_sizes)

    if team_size is not None and starting_slots > team_size:
        raise RuntimeError(
            f"Required champions slot usage ({starting_slots}) exceeds TEAM_SIZE={team_size}."
        )

    base_counts = defaultdict(int)
    team_power = 0.0
    for c in start_team:
        add_champion_traits(base_counts, c, champ_traits, trait_value_overrides)
        team_power += power_map.get(c, 0.0)

    return start_team, base_counts, team_power


def feasibility_check(
    base_counts: Dict[str, int],
    choose_best_emblems,
    required_traits_min: Dict[str, int],
    remaining_slots: int,
    missing_required_one: int,
) -> bool:
    """Check if trait requirements are feasible with remaining team slots.

    Determines whether the required trait minimums can be satisfied given
    the current trait counts, optimal emblem assignment, and remaining
    team slots. A requirement is infeasible if it would need more units
    than slots remaining.

    Parameters
    ----------
    base_counts : Dict[str, int]
        Current trait counts from champions (before emblems).
    choose_best_emblems : callable
        Function that chooses optimal emblems given base counts and missing count.
    required_traits_min : Dict[str, int]
        Minimum trait counts required (after emblems).
    remaining_slots : int
        Number of unit slots remaining on the team.
    missing_required_one : int
        Number of required units still missing (for emblem selection).

    Returns
    -------
    bool
        True if all requirements are feasible, False otherwise.
    """
    if not required_traits_min:
        return True

    emblem_counts = choose_best_emblems(base_counts, missing_required_one)
    effective = compute_effective_counts(base_counts, emblem_counts)

    for t, need_min in required_traits_min.items():
        if need_min <= 0:
            continue
        need = need_min - effective.get(t, 0)
        if need > remaining_slots:
            return False
    return True


def generate_vertical_seeds(
    trait_bps: Dict[str, List[int]],
    playable_champs: List[str],
    champ_traits: Dict[str, List[str]],
    trait_value_overrides: Dict[str, Dict[str, int]],
    slot_sizes: Dict[str, int],
    power_map: Dict[str, float],
    start_team: List[str],
    base_counts0: Dict[str, int],
    team_power0: float,
    team_size: int,
    logger,
) -> List[Tuple[List[str], Dict[str, int], float]]:
    """Generate seed teams focused on reaching high breakpoints for each trait."""
    seeds: List[Tuple[List[str], Dict[str, int], float]] = []
    remaining_slots = team_size - _team_slots(start_team, slot_sizes)
    if remaining_slots <= 0:
        return seeds

    start_team_set = set(start_team)
    seen: Set[Tuple[str, ...]] = set()

    for trait, bps in trait_bps.items():
        candidates = []
        for champ in playable_champs:
            if champ in start_team_set or trait not in champ_traits.get(champ, []):
                continue

            contribution = trait_value_overrides.get(champ, {}).get(trait, 1)
            slot_cost = slot_sizes.get(champ, 1)

            if contribution <= 0 or slot_cost > remaining_slots:
                continue

            candidates.append((champ, contribution, slot_cost, power_map.get(champ, 0.0)))

        if not candidates:
            continue

        candidates.sort(key=lambda x: (-x[1], -x[3]))

        trait_base = base_counts0.get(trait, 0)
        slots_left = remaining_slots
        max_possible = trait_base
        for _champ, contribution, slot_cost, _power in candidates:
            if slot_cost > slots_left:
                continue
            slots_left -= slot_cost
            max_possible += contribution

        target_breakpoints = [bp for bp in bps if trait_base < bp <= max_possible]
        if not target_breakpoints:
            continue

        target = max(target_breakpoints)

        seed_team = list(start_team)
        seed_counts = defaultdict(int, base_counts0)
        seed_power = team_power0
        seed_slots_left = remaining_slots

        for champ, _contribution, slot_cost, champ_power in candidates:
            if seed_slots_left <= 0 or seed_counts.get(trait, 0) >= target:
                break
            seed_team.append(champ)
            add_champion_traits(seed_counts, champ, champ_traits, trait_value_overrides)
            seed_power += champ_power
            seed_slots_left -= slot_cost

        if seed_counts.get(trait, 0) < target:
            continue

        key = tuple(sorted(seed_team))
        if key in seen:
            continue
        seen.add(key)

        seeds.append((seed_team, seed_counts, seed_power))
        logger.log(
            f"seed vertical {trait}→{target}: team={sorted(seed_team)} slots_left={seed_slots_left} trait_count={seed_counts.get(trait)}"
        )

    return seeds
