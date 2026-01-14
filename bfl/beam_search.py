"""Main beam search algorithm and coordination."""

from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Set, Tuple

from bfl.metatft import TraitStat
from bfl.scoring import (
    build_sort_key,
    choose_best_emblems,
    compute_bronze_active,
    score_state,
)
from bfl.team_builder import (
    _team_slots,
    build_required_team,
    feasibility_check,
    generate_vertical_seeds,
)
from bfl.traits import add_champion_traits, apply_emblem_starts, classify_traits


class DecisionLogger:
    """Collect human-readable trace lines for solver decisions."""

    def __init__(self, sink: Optional[List[str]] = None, limit: int = 1500):
        """Initialize a DecisionLogger.

        Parameters
        ----------
        sink : Optional[List[str]]
            List to append log messages to. If None, creates a new list.
        limit : int
            Maximum number of log messages to store (default: 1500).
        """
        self._sink = sink if sink is not None else []
        self._limit = limit

    @property
    def sink(self) -> List[str]:
        """Return the list of logged messages."""
        return self._sink

    def log(self, message: str):
        """Log a decision message.

        Appends the message to the sink list if under the limit.
        Silently ignores messages once the limit is reached.

        Parameters
        ----------
        message : str
            Message to log.
        """
        if len(self._sink) >= self._limit:
            return
        self._sink.append(message)


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
    decision_log: Optional[List[str]] = None,
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

    logger = DecisionLogger(decision_log)
    logger.log(
        f"start: team_size={team_size} beam_width={beam_width} mode={mode} max_emblems={max_emblems_total}"
    )

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

    if banned_champs:
        logger.log(f"banned champions excluded: {sorted(banned_champs)}")

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
        logger.log(f"forced champions: {sorted(forced_units)}")
    playable_champs = [c for c in champs if c not in banned_champs]

    required_one_of = {c for c in required_one_of if c in playable_champs}
    if must_include_one_of and not required_one_of:
        raise RuntimeError(
            "No playable champions available to satisfy must-include-one-of requirement."
        )
    if required_one_of:
        logger.log(f"must include one of: {sorted(required_one_of)}")

    # Validate required traits
    for t, min_count in required_traits_min.items():
        if min_count < 0:
            raise RuntimeError(
                f"Required trait '{t}' minimum cannot be negative (got {min_count})."
            )
        if min_count > 0 and t not in trait_bps:
            raise RuntimeError(
                f"Required trait '{t}' is not in the trait list (trait_bps). Check spelling or set data."
            )
    if required_traits_min:
        logger.log(f"trait minimums: { {t: v for t, v in required_traits_min.items() if v > 0} }")

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

    logger.log(
        "start team: "
        f"{sorted(start_team)} slots={_team_slots(start_team, slot_sizes)} base_counts={dict(base_counts0)} "
        f"team_power={team_power0:.2f}"
    )

    # ----------------------------
    # Emblem helpers
    # ----------------------------
    auto_candidates = sorted([t for t in eligible_traits if t not in hard_emblems])
    bronze_threshold = max(1, min(6, len(eligible_traits)))

    weights = trait_weights or (2.0, 1.0, 0.1)

    # ----------------------------
    # Quality unit heuristics
    # ----------------------------
    # Derive quality thresholds from champions that are actually playable. Using the
    # full set (including banned unlockables) can inflate the threshold so high that
    # no remaining units count as quality, which causes the search to discard every
    # candidate team.
    sorted_power = sorted((power_map.get(c, 0.0) for c in playable_champs), reverse=True)
    if sorted_power:
        quality_threshold = sorted_power[min(6, len(sorted_power) - 1)]
    else:
        quality_threshold = 0.0

    tank_quality_threshold = quality_threshold
    if tank_champions:
        playable_tanks = [ch for ch in tank_champions if ch in playable_champs]
        max_tank_power = max((power_map.get(ch, 0.0) for ch in playable_tanks), default=None)
        if max_tank_power is not None:
            tank_quality_threshold = min(quality_threshold, max_tank_power)

    logger.log(
        f"quality thresholds: carry>={quality_threshold:.2f} tank>={tank_quality_threshold:.2f} eligible_traits={len(eligible_traits)}"
    )

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

    # Create a closure for choose_best_emblems that captures all necessary context
    def choose_best_emblems_closure(
        base_counts: Dict[str, int], missing_required_one: int, team: Optional[List[str]] = None
    ) -> Dict[str, int]:
        return choose_best_emblems(
            base_counts,
            missing_required_one,
            hard_emblems,
            max_emblems_total,
            auto_candidates,
            required_traits_min,
            trait_bps,
            eligible_traits,
            trait_stats,
            weights,
            champ_traits,
            trait_value_overrides,
            power_map,
            tank_champions,
            quality_threshold,
            tank_quality_threshold,
            bronze_threshold,
            team,
        )

    # Create a closure for score_state that captures all necessary context
    def score_state_closure(
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
        return score_state(
            team,
            base_counts,
            missing_required_one,
            hard_emblems,
            max_emblems_total,
            auto_candidates,
            required_traits_min,
            trait_bps,
            eligible_traits,
            trait_stats,
            weights,
            champ_traits,
            trait_value_overrides,
            power_map,
            tank_champions,
            quality_threshold,
            tank_quality_threshold,
            bronze_threshold,
        )

    def add_initial_state(team: List[str], base_counts: Dict[str, int], team_power: float):
        team_set = set(team)
        missing_one = missing_required_one_of(team_set)
        used_slots = _team_slots(team, slot_sizes)
        remaining = team_size - used_slots

        if missing_one and not can_satisfy_required_one_of(team_set, remaining):
            return

        if not feasibility_check(
            base_counts, choose_best_emblems_closure, required_traits_min, remaining, missing_one
        ):
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
        ) = score_state_closure(team, base_counts, missing_one)

        if bronze_threshold >= 6 and bronze + remaining * 3 < bronze_threshold:
            return

        bronze_key = bronze_score
        valid = bronze >= bronze_threshold and qt > 0 and qc > 0 and not missing_quality_trait
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
        logger.log(
            f"seed state: team={sorted(team)} bronze={bronze} active={active} upgraded={upgraded} "
            f"quality={quality_score:.1f} missing_required={missing} missing_one_of={missing_one}"
        )

    # ----------------------------
    # Beam search starting from forced/required team
    # ----------------------------
    # Beam state: (team, base_counts, team_power, sort_key, missing_required_one)
    initial_states: List[Tuple[List[str], Dict[str, int], float, Tuple, int]] = []

    add_initial_state(start_team, base_counts0, team_power0)

    if seed_verticals:
        seeds = generate_vertical_seeds(
            trait_bps,
            playable_champs,
            champ_traits,
            trait_value_overrides,
            slot_sizes,
            power_map,
            start_team,
            base_counts0,
            team_power0,
            team_size,
            logger,
        )
        for seed_team, seed_counts, seed_power in seeds:
            add_initial_state(seed_team, seed_counts, seed_power)

    beam = sorted(initial_states, key=lambda x: x[3], reverse=True)[:beam_width]

    logger.log(f"initial beam size={len(beam)} (width={beam_width})")

    depth = 0
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
                    choose_best_emblems_closure,
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
                ) = score_state_closure(new_team, new_counts, new_missing_required_one)

                if bronze_threshold >= 6 and bronze + new_remaining_slots * 3 < bronze_threshold:
                    continue

                bronze_key = bronze_score
                valid = (
                    bronze >= bronze_threshold and qt > 0 and qc > 0 and not missing_quality_trait
                )

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
                candidates.append(
                    (new_team, new_counts, new_power, new_key, new_missing_required_one)
                )
                progressed = True

        if not candidates:
            break

        candidates.sort(key=lambda x: x[3], reverse=True)
        beam = candidates[:beam_width]

        if beam:
            top_team, top_counts, _, _, top_missing_one = beam[0]
            top_emblem_counts = choose_best_emblems_closure(top_counts, top_missing_one, top_team)
            top_counts_with_emblems = apply_emblem_starts(top_counts, top_emblem_counts)
            top_bronze, top_active, top_upgraded = compute_bronze_active(
                top_counts_with_emblems, trait_bps, eligible_traits
            )
            logger.log(
                f"depth {depth}: advanced to {len(beam)} states; best bronze={top_bronze} active={top_active} upgraded={top_upgraded} team={sorted(top_team)}"
            )

        if not progressed:
            break

        depth += 1

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
        ) = score_state_closure(team, base_counts, missing_required_one)

        if (
            bronze_threshold >= 6
            and bronze + (team_size - _team_slots(team, slot_sizes)) * 3 < bronze_threshold
        ):
            continue

        bronze_key = bronze_score
        valid = bronze >= bronze_threshold and qt > 0 and qc > 0 and not missing_quality_trait

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

        evaluated_states.append(
            (team, base_counts, team_power, new_key, missing_required_one, valid)
        )

    if required_one_of:
        evaluated_states = [state for state in evaluated_states if state[4] == 0]
        if not evaluated_states:
            raise RuntimeError(
                "No team satisfies the must-include-one-of requirement under current constraints."
            )

    valid_states = [state for state in evaluated_states if state[5]]
    logger.log(
        f"final evaluation: {len(evaluated_states)} states scored, {len(valid_states)} valid (bronze>={bronze_threshold}, quality tank/carry)"
    )
    if not valid_states and evaluated_states:
        fallback_state = max(evaluated_states, key=lambda x: x[3])
        logger.log(
            "No teams met the bronze threshold; returning the best available candidate below the target instead."
        )
        valid_states = [fallback_state]
    if not valid_states:
        raise RuntimeError(
            "Beam search produced teams, but none met the Bronze-for-Life validity gates (bronze>=threshold with quality tank/carry)."
        )

    best_team, best_base_counts, best_power, _best_key, best_missing_required_one, _ = max(
        valid_states, key=lambda x: x[3]
    )

    emblem_counts = choose_best_emblems_closure(
        best_base_counts, best_missing_required_one, best_team
    )

    counts, bronze_traits, active_traits, upgraded_traits, used_traits = classify_traits(
        best_team, champ_traits, trait_bps, eligible_traits, emblem_counts, trait_value_overrides
    )

    logger.log(
        "selected team: "
        f"{sorted(best_team)} bronze={len(bronze_traits)} active={len(active_traits)} upgraded={len(upgraded_traits)} "
        f"emblems={emblem_counts} team_power={best_power:.2f}"
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
