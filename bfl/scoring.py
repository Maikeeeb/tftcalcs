"""Scoring and evaluation logic for beam search."""

from collections import defaultdict
from typing import Callable, Dict, List, Optional, Set, Tuple

from bfl.metatft import TraitStat, trait_power
from bfl.traits import apply_emblem_starts


def bronze_piecewise_score(bronze: int, bronze_threshold: int) -> float:
    """Compute bronze score with piecewise function."""
    if bronze < bronze_threshold:
        return -(bronze_threshold - bronze) * 50.0
    if bronze >= 10:
        return 225.0
    mapping = {6: 100.0, 7: 160.0, 8: 200.0, 9: 215.0}
    return mapping.get(bronze, 200.0)


def compute_bronze_active(
    counts_with_emblems: Dict[str, int],
    trait_bps: Dict[str, List[int]],
    eligible_traits: Set[str],
) -> Tuple[int, int, int]:
    """Compute bronze count, active traits count, and upgraded traits count."""
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


def compute_trait_score(
    counts_with_emblems: Dict[str, int],
    trait_stats: Optional[Dict[str, List[TraitStat]]],
    weights: Tuple[float, float, float],
) -> float:
    """Compute MetaTFT trait score."""
    if not trait_stats:
        return 0.0
    w_win, w_avg, w_freq = weights
    score = 0.0
    for trait in trait_stats:
        score += trait_power(
            trait, counts_with_emblems.get(trait, 0), trait_stats, w_win, w_avg, w_freq
        )
    return score


def is_trait_active(
    counts_with_emblems: Dict[str, int],
    trait: str,
    trait_bps: Dict[str, List[int]],
    eligible_traits: Set[str],
) -> bool:
    """Check if a trait is active at its first breakpoint."""
    # Personal/exclusive traits (not in ``eligible_traits``) should never
    # satisfy quality checks. Only traits that can contribute to bronze are
    # considered for "trait active" checks here.
    if trait not in eligible_traits:
        return False

    bp = trait_bps.get(trait, [1])[0]
    return counts_with_emblems.get(trait, 0) >= bp


def is_quality_unit(
    champ: str,
    counts_with_emblems: Dict[str, int],
    champ_traits: Dict[str, List[str]],
    trait_bps: Dict[str, List[int]],
    eligible_traits: Set[str],
    trait_value_overrides: Dict[str, Dict[str, int]],
    power_map: Dict[str, float],
    tank_champions: Set[str],
    quality_threshold: float,
    tank_quality_threshold: float,
) -> bool:
    """Check if a unit is quality (meets power threshold and activates traits)."""
    power = power_map.get(champ, 0.0)
    threshold = tank_quality_threshold if champ in tank_champions else quality_threshold
    if power < threshold:
        return False

    champ_traits_list = champ_traits.get(champ, [])
    positive_traits = [
        trait
        for trait in champ_traits_list
        if trait_value_overrides.get(champ, {}).get(trait, 1) > 0 and trait in eligible_traits
    ]

    # Allow completely traitless champions (e.g., Ryze) to qualify as quality
    # tanks/carries based solely on power. Units that *have* traits must still
    # activate at least one of them.
    if not positive_traits:
        return True

    return any(
        is_trait_active(counts_with_emblems, trait, trait_bps, eligible_traits)
        for trait in positive_traits
    )


def quality_summary(
    team: List[str],
    counts_with_emblems: Dict[str, int],
    champ_traits: Dict[str, List[str]],
    trait_bps: Dict[str, List[int]],
    eligible_traits: Set[str],
    trait_value_overrides: Dict[str, Dict[str, int]],
    power_map: Dict[str, float],
    tank_champions: Set[str],
    quality_threshold: float,
    tank_quality_threshold: float,
) -> Tuple[int, int, float, bool]:
    """Summarize quality tanks, carries, total quality score, and missing trait flag."""
    quality_tanks = 0
    quality_carries = 0
    quality_score = 0.0
    quality_missing_trait = False

    for champ in team:
        power = power_map.get(champ, 0.0)
        traits = champ_traits.get(champ, [])
        positive_traits = [
            trait
            for trait in traits
            if trait_value_overrides.get(champ, {}).get(trait, 1) > 0 and trait in eligible_traits
        ]
        activates_trait = any(
            is_trait_active(counts_with_emblems, trait, trait_bps, eligible_traits)
            for trait in positive_traits
        )
        threshold = tank_quality_threshold if champ in tank_champions else quality_threshold
        if power >= threshold and positive_traits and not activates_trait:
            quality_missing_trait = True
        if not is_quality_unit(
            champ,
            counts_with_emblems,
            champ_traits,
            trait_bps,
            eligible_traits,
            trait_value_overrides,
            power_map,
            tank_champions,
            quality_threshold,
            tank_quality_threshold,
        ):
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


def bronze_penalty(
    team: List[str],
    counts_with_emblems: Dict[str, int],
    champ_traits: Dict[str, List[str]],
    trait_bps: Dict[str, List[int]],
    eligible_traits: Set[str],
    power_map: Dict[str, float],
    quality_threshold: float,
) -> float:
    """Penalize bronze traits composed entirely of low-quality units."""
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
    """Build sort key for beam search states."""
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
    base_counts: Dict[str, int],
    missing_required_one: int,
    hard_emblems: Dict[str, int],
    max_emblems_total: int,
    auto_candidates: List[str],
    required_traits_min: Dict[str, int],
    trait_bps: Dict[str, List[int]],
    eligible_traits: Set[str],
    trait_stats: Optional[Dict[str, List[TraitStat]]],
    weights: Tuple[float, float, float],
    champ_traits: Dict[str, List[str]],
    trait_value_overrides: Dict[str, Dict[str, int]],
    power_map: Dict[str, float],
    tank_champions: Set[str],
    quality_threshold: float,
    tank_quality_threshold: float,
    bronze_threshold: int,
    team: Optional[List[str]] = None,
) -> Dict[str, int]:
    """Choose optimal emblem combination to maximize team score.

    Greedily selects emblems from auto_candidates to maximize the team's
    overall score, considering bronze count, trait scores, quality units,
    and requirement satisfaction.

    Parameters
    ----------
    base_counts : Dict[str, int]
        Base trait counts from champions (before emblems).
    missing_required_one : int
        Number of required units still missing.
    hard_emblems : Dict[str, int]
        Fixed emblem counts that must be included.
    max_emblems_total : int
        Maximum total emblems allowed (hard + auto).
    auto_candidates : List[str]
        Traits available for automatic emblem assignment.
    required_traits_min : Dict[str, int]
        Minimum trait counts required.
    trait_bps : Dict[str, List[int]]
        Trait breakpoint lists.
    eligible_traits : Set[str]
        Traits eligible for Bronze for Life.
    trait_stats : Optional[Dict[str, List[TraitStat]]]
        MetaTFT trait statistics (for standard mode).
    weights : Tuple[float, float, float]
        MetaTFT weights (w_win, w_avg, w_freq).
    champ_traits : Dict[str, List[str]]
        Champion to traits mapping.
    trait_value_overrides : Dict[str, Dict[str, int]]
        Per-champion trait value overrides.
    power_map : Dict[str, float]
        Champion power scores.
    tank_champions : Set[str]
        Set of tank champion apiNames.
    quality_threshold : float
        Minimum power for quality carry units.
    tank_quality_threshold : float
        Minimum power for quality tank units.
    bronze_threshold : int
        Minimum bronze count required.
    team : Optional[List[str]]
        Current team composition (for quality/penalty calculations).

    Returns
    -------
    Dict[str, int]
        Optimal emblem counts per trait (includes hard_emblems).
    """
    if max_emblems_total <= 0:
        return dict(hard_emblems)

    chosen = dict(hard_emblems)

    def eval_with(chosen_emblems: Dict[str, int]) -> Tuple[int, int, int, int, Tuple]:
        cnt2 = apply_emblem_starts(base_counts, chosen_emblems)
        bronze, active, upgraded = compute_bronze_active(cnt2, trait_bps, eligible_traits)

        from bfl.team_builder import requirement_gap

        missing_requirements = requirement_gap(required_traits_min, cnt2)
        trait_score = compute_trait_score(cnt2, trait_stats, weights)
        qt, qc, quality_score, missing_traits = quality_summary(
            team or [],
            cnt2,
            champ_traits,
            trait_bps,
            eligible_traits,
            trait_value_overrides,
            power_map,
            tank_champions,
            quality_threshold,
            tank_quality_threshold,
        )
        penalty = bronze_penalty(
            team or [],
            cnt2,
            champ_traits,
            trait_bps,
            eligible_traits,
            power_map,
            quality_threshold,
        )
        bronze_score = bronze_piecewise_score(bronze, bronze_threshold)
        valid = bronze >= bronze_threshold and qt > 0 and qc > 0 and not missing_traits
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

    bronze0, _active0, _upgraded0, _missing0, key0 = eval_with(chosen)

    for t in auto_candidates:
        if remaining == 0:
            break
        remaining -= 1

        trial = dict(chosen)
        trial[t] = trial.get(t, 0) + 1

        bronze, active, upgraded, missing, key = eval_with(trial)
        if key > key0:
            key0 = key
            bronze0 = bronze
            chosen = trial

    return chosen


def score_state(
    team: List[str],
    base_counts: Dict[str, int],
    missing_required_one: int,
    hard_emblems: Dict[str, int],
    max_emblems_total: int,
    auto_candidates: List[str],
    required_traits_min: Dict[str, int],
    trait_bps: Dict[str, List[int]],
    eligible_traits: Set[str],
    trait_stats: Optional[Dict[str, List[TraitStat]]],
    weights: Tuple[float, float, float],
    champ_traits: Dict[str, List[str]],
    trait_value_overrides: Dict[str, Dict[str, int]],
    power_map: Dict[str, float],
    tank_champions: Set[str],
    quality_threshold: float,
    tank_quality_threshold: float,
    bronze_threshold: int,
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
    """Score a team state and return comprehensive metrics.

    Computes all scoring metrics for a team state including bronze count,
    trait scores, quality units, penalties, and requirement satisfaction.
    Chooses optimal emblems before scoring.

    Parameters
    ----------
    team : List[str]
        List of champion apiNames on the team.
    base_counts : Dict[str, int]
        Base trait counts from champions (before emblems).
    missing_required_one : int
        Number of required units still missing.
    hard_emblems : Dict[str, int]
        Fixed emblem counts that must be included.
    max_emblems_total : int
        Maximum total emblems allowed.
    auto_candidates : List[str]
        Traits available for automatic emblem assignment.
    required_traits_min : Dict[str, int]
        Minimum trait counts required.
    trait_bps : Dict[str, List[int]]
        Trait breakpoint lists.
    eligible_traits : Set[str]
        Traits eligible for Bronze for Life.
    trait_stats : Optional[Dict[str, List[TraitStat]]]
        MetaTFT trait statistics (for standard mode).
    weights : Tuple[float, float, float]
        MetaTFT weights (w_win, w_avg, w_freq).
    champ_traits : Dict[str, List[str]]
        Champion to traits mapping.
    trait_value_overrides : Dict[str, Dict[str, int]]
        Per-champion trait value overrides.
    power_map : Dict[str, float]
        Champion power scores.
    tank_champions : Set[str]
        Set of tank champion apiNames.
    quality_threshold : float
        Minimum power for quality carry units.
    tank_quality_threshold : float
        Minimum power for quality tank units.
    bronze_threshold : int
        Minimum bronze count required.

    Returns
    -------
    Tuple[int, int, int, int, Dict[str, int], float, float, float, bool, float, int, int]
        Tuple containing:
        - Bronze count (eligible traits at first breakpoint)
        - Active traits count (any breakpoint)
        - Upgraded traits count (second breakpoint or higher)
        - Missing requirements gap (total missing trait stacks)
        - Optimal emblem counts
        - Trait score (MetaTFT-based)
        - Quality score (sum of quality unit powers)
        - Bronze penalty (for fake bronze traits)
        - Missing quality trait flag (quality unit without active trait)
        - Bronze piecewise score
        - Quality tanks count
        - Quality carries count
    """
    emblem_counts = choose_best_emblems(
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
    cnt2 = apply_emblem_starts(base_counts, emblem_counts)

    bronze, active, upgraded = compute_bronze_active(cnt2, trait_bps, eligible_traits)

    from bfl.team_builder import requirement_gap

    missing_requirements = requirement_gap(required_traits_min, cnt2)
    trait_score = compute_trait_score(cnt2, trait_stats, weights)
    quality_tanks, quality_carries, quality_score, missing_quality_trait = quality_summary(
        team,
        cnt2,
        champ_traits,
        trait_bps,
        eligible_traits,
        trait_value_overrides,
        power_map,
        tank_champions,
        quality_threshold,
        tank_quality_threshold,
    )
    penalty = bronze_penalty(
        team,
        cnt2,
        champ_traits,
        trait_bps,
        eligible_traits,
        power_map,
        quality_threshold,
    )
    bronze_score = bronze_piecewise_score(bronze, bronze_threshold)

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
