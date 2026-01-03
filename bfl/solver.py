from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Set, Tuple

from bfl.metatft import TraitStat, trait_power
from bfl.traits import add_champion_traits, apply_emblem_starts, classify_traits


def _team_slots(team: List[str], champ_slot_sizes: Dict[str, int]) -> int:
    return sum(champ_slot_sizes.get(c, 1) for c in team)


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
    trait_stats: Optional[Dict[str, List[TraitStat]]] = None,
    tank_champions: Optional[Set[str]] = None,
    mode: str = "bronze",
    trait_weights: Tuple[float, float, float] | None = None,
    champ_slot_sizes: Optional[Dict[str, int]] = None,
    trait_value_overrides: Optional[Dict[str, Dict[str, int]]] = None,
    must_include_one_of: Optional[Set[str]] = None,
    seed_verticals: bool = True,
):
    """
    Beam search for teams with either max bronze-active traits (bronze mode) or
    highest MetaTFT trait score (standard mode), with emblems.

    Bronze mode tie-breakers (in this order):
      1) bronze count (eligible, tier1-only)
      2) active eligible traits (any tier)
      3) fewer upgraded (tier2+)
      4) higher team power (from MetaTFT)

    Standard mode uses MetaTFT trait scores as the primary objective followed by
    active/bronze counts and team power.

    forced_units:
      Optional iterable of champion apiNames that MUST be included in the final team.
      Example: ["TFT16_Alpha", "TFT16_Beta"]

    seed_verticals:
      When enabled, prime the initial beam with vertical-focused teams aimed at the
      highest reachable breakpoint for each trait. This helps the search consider
      far-off breakpoints (e.g., Void 9) even when early partial teams look weak.
    """

    required_traits_min = required_traits_min or {}
    required_map = required_champions or {}
    slot_sizes = champ_slot_sizes or {}
    trait_value_overrides = trait_value_overrides or {}
    tank_champions = tank_champions or set()
    banned_champs = {c for c, flag in required_map.items() if flag < 0}
    champs_set = set(champs)
    required_one_of = set(must_include_one_of or set())

    missing_banned = banned_champs - champs_set
    if missing_banned:
        raise RuntimeError(
            f"Banned champions not in playable pool: {sorted(missing_banned)}. Check spelling or filtering."
        )

    if forced_units:
        forced_units = list(forced_units)
        banned_forced = [c for c in forced_units if c in banned_champs]
        if banned_forced:
            raise RuntimeError(
                f"Forced champions cannot be banned: {banned_forced}. Update required_champions or forced_units."
            )
        missing_forced = [c for c in forced_units if c not in champs_set]
        if missing_forced:
            raise RuntimeError(
                f"Forced champions not in playable pool: {missing_forced}. Check name or filtering."
            )
    playable_champs = [c for c in champs if c not in banned_champs]

    required_one_of = {c for c in required_one_of if c in playable_champs}
    if must_include_one_of and not required_one_of:
        raise RuntimeError("No playable champions available to satisfy must-include-one-of requirement.")

    # Validate required traits
    for t, min_count in required_traits_min.items():
        if min_count < 0:
            raise RuntimeError(f"Required trait '{t}' minimum cannot be negative (got {min_count}).")
        if min_count > 0 and t not in trait_bps:
            raise RuntimeError(
                f"Required trait '{t}' is not in the trait list (trait_bps). Check spelling or set data."
            )

    if team_size is not None and len(playable_champs) < team_size:
        raise RuntimeError(
            f"Not enough playable units after banning champions: {len(playable_champs)} (need {team_size})."
        )

    start_team, base_counts0, team_power0 = build_required_team(
        champs,
        champ_traits,
        power_map,
        required_champions,
        slot_sizes,
        trait_value_overrides,
        forced_units,
        team_size,
    )

    # ----------------------------
    # Emblem helpers
    # ----------------------------
    auto_candidates = sorted([t for t in eligible_traits if t not in hard_emblems])

    weights = trait_weights or (2.0, 1.0, 0.1)

    # ----------------------------
    # Quality unit heuristics
    # ----------------------------
    sorted_power = sorted(power_map.values(), reverse=True)
    if sorted_power:
        quality_threshold = sorted_power[min(6, len(sorted_power) - 1)]
    else:
        quality_threshold = 0.0

    def missing_required_one_of(team_set: Set[str]) -> int:
        if not required_one_of:
            return 0
        return 0 if required_one_of.intersection(team_set) else 1

    def can_satisfy_required_one_of(team_set: Set[str], remaining_slots: int) -> bool:
        if missing_required_one_of(team_set) == 0:
            return True
        return any(
            c not in team_set and slot_sizes.get(c, 1) <= remaining_slots for c in required_one_of
        )

    def compute_trait_score(counts_with_emblems: Dict[str, int]) -> float:
        if not trait_stats:
            return 0.0
        w_win, w_avg, w_freq = weights
        score = 0.0
        for trait in trait_stats:
            score += trait_power(
                trait, counts_with_emblems.get(trait, 0), trait_stats, w_win, w_avg, w_freq
            )
        return score

    def is_trait_active(counts_with_emblems: Dict[str, int], trait: str) -> bool:
        # Personal/exclusive traits (not in ``eligible_traits``) should never
        # satisfy quality checks. Only traits that can contribute to bronze are
        # considered for "trait active" checks here.
        if trait not in eligible_traits:
            return False

        bp = trait_bps.get(trait, [1])[0]
        return counts_with_emblems.get(trait, 0) >= bp

    def is_quality_unit(champ: str, counts_with_emblems: Dict[str, int]) -> bool:
        power = power_map.get(champ, 0.0)
        if power < quality_threshold:
            return False
        champ_traits_list = champ_traits.get(champ, [])
        for trait in champ_traits_list:
            contribution = trait_value_overrides.get(champ, {}).get(trait, 1)
            if contribution <= 0:
                continue
            if is_trait_active(counts_with_emblems, trait):
                return True
        return False

    def quality_summary(team: List[str], counts_with_emblems: Dict[str, int]) -> Tuple[int, int, float, bool]:
        quality_tanks = 0
        quality_carries = 0
        quality_score = 0.0
        quality_missing_trait = False

        for champ in team:
            power = power_map.get(champ, 0.0)
            traits = champ_traits.get(champ, [])
            activates_trait = any(
                trait_value_overrides.get(champ, {}).get(trait, 1) > 0 and is_trait_active(counts_with_emblems, trait)
                for trait in traits
            )
            if power >= quality_threshold and not activates_trait:
                quality_missing_trait = True
            if not is_quality_unit(champ, counts_with_emblems):
                continue
            quality_score += power
            is_tank = champ in tank_champions if tank_champions else True
            if is_tank:
                quality_tanks += 1
                if not tank_champions:
                    quality_carries += 1
            else:
                quality_carries += 1

        return quality_tanks, quality_carries, quality_score, quality_missing_trait

    def bronze_penalty(team: List[str], counts_with_emblems: Dict[str, int]) -> float:
        penalty = 0.0
        for trait in eligible_traits:
            bps = trait_bps[trait]
            count = counts_with_emblems.get(trait, 0)
            if count < bps[0]:
                continue
            if len(bps) > 1 and count >= bps[1]:
                continue
            units_with_trait = [champ for champ in team if trait in champ_traits.get(champ, [])]
            if not units_with_trait:
                continue
            best_power = max(power_map.get(ch, 0.0) for ch in units_with_trait)
            if best_power < quality_threshold:
                penalty += 5.0
        return penalty

    def bronze_piecewise_score(bronze: int) -> float:
        if bronze < 6:
            return float("-inf")
        if bronze >= 10:
            return 225.0
        mapping = {6: 100.0, 7: 160.0, 8: 200.0, 9: 215.0}
        return mapping.get(bronze, 200.0)

    def compute_bronze_active(counts_with_emblems: Dict[str, int]) -> Tuple[int, int, int]:
        bronze = 0
        active = 0
        upgraded = 0

        for t in eligible_traits:
            bps = trait_bps[t]
            c = counts_with_emblems.get(t, 0)
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

    def build_sort_key(
        valid: bool,
        missing_required_one: int,
        missing_requirements: int,
        bronze: int,
        bronze_score: float,
        quality_score: float,
        penalty: float,
        active: int,
        upgraded: int,
        power: float,
        trait_score: float,
    ) -> Tuple:
        return (
            1 if valid else 0,
            -missing_required_one,
            -missing_requirements,
            bronze_score,
            quality_score,
            -penalty,
            trait_score,
            active,
            bronze,
            -upgraded,
            power,
        )

    def choose_best_emblems(
        base_counts: Dict[str, int], missing_required_one: int, team: Optional[List[str]] = None
    ) -> Dict[str, int]:
        if max_emblems_total <= 0:
            return dict(hard_emblems)

        chosen = dict(hard_emblems)

        def eval_with(chosen_emblems: Dict[str, int]) -> Tuple[int, int, int, int, Tuple]:
            cnt2 = apply_emblem_starts(base_counts, chosen_emblems)
            bronze, active, upgraded = compute_bronze_active(cnt2)
            missing_requirements = requirement_gap(required_traits_min, cnt2)
            trait_score = compute_trait_score(cnt2)
            qt, qc, quality_score, missing_traits = quality_summary(team or [], cnt2)
            penalty = bronze_penalty(team or [], cnt2)
            bronze_score = bronze_piecewise_score(bronze)
            valid = (
                bronze_score != float("-inf")
                and qt > 0
                and qc > 0
                and not missing_traits
            )
            key = build_sort_key(
                valid,
                missing_required_one,
                missing_requirements,
                bronze,
                bronze_score,
                quality_score,
                penalty,
                active,
                upgraded,
                0.0,
                trait_score,
            )
            return bronze, active, upgraded, missing_requirements, key

        already_used = sum(chosen.values())
        remaining = max(0, max_emblems_total - already_used)
        if remaining == 0:
            return chosen

        bronze0, active0, upgraded0, missing0, key0 = eval_with(chosen)

        for t in auto_candidates:
            if remaining == 0:
                break
            remaining -= 1

            trial = dict(chosen)
            trial[t] = trial.get(t, 0) + 1

            bronze, active, upgraded, missing, key = eval_with(trial)
            if key > key0:
                key0 = key
                bronze0, active0, upgraded0, missing0 = bronze, active, upgraded, missing
                chosen = trial

        return chosen

    def score_state(
        team: List[str], base_counts: Dict[str, int], missing_required_one: int
    ) -> Tuple[
        int,
        int,
        int,
        int,
        Dict[str, int],
        float,
        float,
        float,
        bool,
        float,
        int,
        int,
    ]:
        emblem_counts = choose_best_emblems(base_counts, missing_required_one, team)
        cnt2 = apply_emblem_starts(base_counts, emblem_counts)

        bronze, active, upgraded = compute_bronze_active(cnt2)
        missing_requirements = requirement_gap(required_traits_min, cnt2)
        trait_score = compute_trait_score(cnt2)
        quality_tanks, quality_carries, quality_score, missing_quality_trait = quality_summary(team, cnt2)
        penalty = bronze_penalty(team, cnt2)
        bronze_score = bronze_piecewise_score(bronze)

        return (
            bronze,
            active,
            upgraded,
            missing_requirements,
            emblem_counts,
            trait_score,
            quality_score,
            penalty,
            missing_quality_trait,
            bronze_score,
            quality_tanks,
            quality_carries,
        )

    def generate_vertical_seeds() -> List[Tuple[List[str], Dict[str, int], float]]:
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

        return seeds

    def add_initial_state(team: List[str], base_counts: Dict[str, int], team_power: float):
        team_set = set(team)
        missing_one = missing_required_one_of(team_set)
        used_slots = _team_slots(team, slot_sizes)
        remaining = team_size - used_slots

        if missing_one and not can_satisfy_required_one_of(team_set, remaining):
            return

        if not feasibility_check(base_counts, choose_best_emblems, required_traits_min, remaining, missing_one):
            return

        (
            bronze,
            active,
            upgraded,
            missing,
            _,
            trait_score,
            quality_score,
            penalty,
            missing_quality_trait,
            bronze_score,
            qt,
            qc,
        ) = score_state(team, base_counts, missing_one)

        if bronze + remaining * 3 < 6:
            return

        bronze_key = bronze_score if bronze_score != float("-inf") else -1e9
        valid = bronze_score != float("-inf") and qt > 0 and qc > 0 and not missing_quality_trait
        sort_key = build_sort_key(
            valid,
            missing_one,
            missing,
            bronze,
            bronze_key,
            quality_score,
            penalty,
            active,
            upgraded,
            team_power,
            trait_score,
        )

        initial_states.append((team, base_counts, team_power, sort_key, missing_one))

    # ----------------------------
    # Beam search starting from forced/required team
    # ----------------------------
    # Beam state: (team, base_counts, team_power, sort_key, missing_required_one)
    initial_states: List[Tuple[List[str], Dict[str, int], float, Tuple, int]] = []

    add_initial_state(start_team, base_counts0, team_power0)

    if seed_verticals:
        for seed_team, seed_counts, seed_power in generate_vertical_seeds():
            add_initial_state(seed_team, seed_counts, seed_power)

    beam = sorted(initial_states, key=lambda x: x[3], reverse=True)[:beam_width]

    while True:
        candidates = []
        progressed = False
        for team, base_counts, team_power, key, missing_required_one in beam:
            team_set = set(team)
            current_slots = _team_slots(team, slot_sizes)
            remaining_slots = team_size - current_slots
            if remaining_slots <= 0:
                candidates.append((team, base_counts, team_power, key, missing_required_one))
                continue

            for c in playable_champs:
                if c in team_set:
                    continue

                slot_cost = slot_sizes.get(c, 1)
                if slot_cost > remaining_slots:
                    continue

                new_team = team + [c]
                new_counts = defaultdict(int, base_counts)
                add_champion_traits(new_counts, c, champ_traits, trait_value_overrides)

                new_power = team_power + power_map.get(c, 0.0)
                new_remaining_slots = remaining_slots - slot_cost

                new_team_set = team_set | {c}
                new_missing_required_one = missing_required_one_of(new_team_set)

                if new_missing_required_one and not can_satisfy_required_one_of(
                    new_team_set, new_remaining_slots
                ):
                    continue

                if not feasibility_check(
                    new_counts,
                    choose_best_emblems,
                    required_traits_min,
                    new_remaining_slots,
                    new_missing_required_one,
                ):
                    continue

                (
                    bronze,
                    active,
                    upgraded,
                    missing,
                    _,
                    trait_score,
                    quality_score,
                    penalty,
                    missing_quality_trait,
                    bronze_score,
                    qt,
                    qc,
                ) = score_state(new_team, new_counts, new_missing_required_one)

                if bronze + new_remaining_slots * 3 < 6:
                    continue

                bronze_key = bronze_score if bronze_score != float("-inf") else -1e9
                valid = bronze_score != float("-inf") and qt > 0 and qc > 0 and not missing_quality_trait

                new_key = build_sort_key(
                    valid,
                    new_missing_required_one,
                    missing,
                    bronze,
                    bronze_key,
                    quality_score,
                    penalty,
                    active,
                    upgraded,
                    new_power,
                    trait_score,
                )
                candidates.append((new_team, new_counts, new_power, new_key, new_missing_required_one))
                progressed = True

        if not candidates:
            break

        candidates.sort(key=lambda x: x[3], reverse=True)
        beam = candidates[:beam_width]

        if not progressed:
            break

    if not beam:
        raise RuntimeError(
            "Beam search produced no candidates under the given constraints. Check filtering/requirements."
        )

    evaluated_states = []
    for team, base_counts, team_power, _key, missing_required_one in beam:
        (
            bronze,
            active,
            upgraded,
            missing,
            _emblems,
            trait_score,
            quality_score,
            penalty,
            missing_quality_trait,
            bronze_score,
            qt,
            qc,
        ) = score_state(team, base_counts, missing_required_one)

        if bronze + (team_size - _team_slots(team, slot_sizes)) * 3 < 6:
            continue

        bronze_key = bronze_score if bronze_score != float("-inf") else -1e9
        valid = bronze_score != float("-inf") and qt > 0 and qc > 0 and not missing_quality_trait

        new_key = build_sort_key(
            valid,
            missing_required_one,
            missing,
            bronze,
            bronze_key,
            quality_score,
            penalty,
            active,
            upgraded,
            team_power,
            trait_score,
        )

        evaluated_states.append((team, base_counts, team_power, new_key, missing_required_one, valid))

    if required_one_of:
        evaluated_states = [state for state in evaluated_states if state[4] == 0]
        if not evaluated_states:
            raise RuntimeError("No team satisfies the must-include-one-of requirement under current constraints.")

    valid_states = [state for state in evaluated_states if state[5]]
    if not valid_states:
        raise RuntimeError(
            "Beam search produced teams, but none met the Bronze-for-Life validity gates (bronze>=6 with quality tank/carry)."
        )

    best_team, best_base_counts, best_power, _best_key, best_missing_required_one, _ = max(
        valid_states, key=lambda x: x[3]
    )

    emblem_counts = choose_best_emblems(best_base_counts, best_missing_required_one, best_team)

    counts, bronze_traits, active_traits, upgraded_traits, used_traits = classify_traits(
        best_team, champ_traits, trait_bps, eligible_traits, emblem_counts, trait_value_overrides
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
