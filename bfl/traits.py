from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple


def add_champion_traits(
    counts: Dict[str, int],
    champion: str,
    champ_traits: Dict[str, List[str]],
    trait_value_overrides: Optional[Dict[str, Dict[str, int]]] = None,
) -> None:
    """Increment ``counts`` for each trait on ``champion``.

    Parameters
    ----------
    counts: Dict[str, int]
        Mutable trait counter to update.
    champion: str
        apiName of the champion whose traits should be added.
    champ_traits: Dict[str, List[str]]
        Mapping of champion apiName to their trait list.
    trait_value_overrides: Optional[Dict[str, Dict[str, int]]]
        Optional per-champion overrides for how many stacks each trait
        contributes. When omitted, each trait counts as ``1``. Values are
        looked up as ``trait_value_overrides[champion][trait]``.
    """

    overrides = (trait_value_overrides or {}).get(champion, {})
    for trait in champ_traits[champion]:
        counts[trait] += overrides.get(trait, 1)


def apply_emblem_starts(counts: Dict[str, int], emblem_counts: Dict[str, int]) -> Dict[str, int]:
    """Apply emblem counts to base trait counts.

    Adds emblem contributions to trait counts. Returns a new dictionary
    with the combined counts.

    Parameters
    ----------
    counts : Dict[str, int]
        Base trait counts from champions.
    emblem_counts : Dict[str, int]
        Additional counts from emblems per trait.

    Returns
    -------
    Dict[str, int]
        Combined trait counts after applying emblems.
    """
    out = defaultdict(int, counts)
    for t, v in emblem_counts.items():
        out[t] += v
    return dict(out)


def classify_traits(
    team: List[str],
    champ_traits: Dict[str, List[str]],
    trait_bps: Dict[str, List[int]],
    eligible_traits: Set[str],
    emblem_counts: Dict[str, int],
    trait_value_overrides: Optional[Dict[str, Dict[str, int]]] = None,
) -> Tuple[Dict[str, int], List[str], List[str], List[str], List[str]]:
    """Classify traits into bronze, active, and upgraded categories.

    Computes trait counts from the team and emblems, then categorizes eligible
    traits based on their breakpoints.

    Parameters
    ----------
    team : List[str]
        List of champion apiNames on the team.
    champ_traits : Dict[str, List[str]]
        Mapping of champion apiName to their trait list.
    trait_bps : Dict[str, List[int]]
        Mapping of trait names to sorted breakpoint lists.
    eligible_traits : Set[str]
        Traits that are eligible for Bronze for Life (appear on 2+ champions).
    emblem_counts : Dict[str, int]
        Additional counts from emblems per trait.
    trait_value_overrides : Optional[Dict[str, Dict[str, int]]]
        Optional per-champion overrides for trait contribution values.

    Returns
    -------
    Tuple[Dict[str, int], List[str], List[str], List[str], List[str]]
        Tuple containing:
        - Effective trait counts (after emblems)
        - Bronze traits (at first breakpoint only)
        - Active traits (any breakpoint)
        - Upgraded traits (second breakpoint or higher)
        - All traits used by the team (sorted)
    """
    # base counts from team
    cnt = defaultdict(int)
    for c in team:
        add_champion_traits(cnt, c, champ_traits, trait_value_overrides)

    # add emblem starts
    cnt2 = apply_emblem_starts(cnt, emblem_counts)

    bronze = []
    active_any = []
    upgraded = []

    for t in eligible_traits:
        bps = trait_bps[t]
        c = cnt2.get(t, 0)
        if c < bps[0]:
            continue

        active_any.append(t)

        if len(bps) == 1:
            bronze.append(t)
        else:
            if c < bps[1]:
                bronze.append(t)
            else:
                upgraded.append(t)

    used = sorted({t for c in team for t in champ_traits[c]})
    return dict(cnt2), sorted(bronze), sorted(active_any), sorted(upgraded), used
