from collections import defaultdict
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


def load_set_data(
    path: str | Path,
    set_id: str,
    blacklist_traits: Optional[Set[str]] = None,
) -> Tuple[
    Dict,
    List[str],
    Dict[str, List[str]],
    Dict[str, List[int]],
    Dict[str, int],
    Set[str],
    Dict[str, int],
]:
    """Load and parse TFT set data from Riot's JSON format.

    Extracts champions, traits, breakpoints, and eligibility information from
    the official set data file. Filters out non-playable units and determines
    which traits are eligible for Bronze for Life.

    Parameters
    ----------
    path : str | Path
        Path to the Riot set data JSON file (e.g., en_us.json).
    set_id : str
        Set identifier within the JSON file (e.g., "16" for Set 16).
    blacklist_traits : Optional[Set[str]]
        Traits to exclude from eligibility even if they meet other criteria.

    Returns
    -------
    Tuple[Dict, List[str], Dict[str, List[str]], Dict[str, List[int]], Dict[str, int], Set[str], Dict[str, int]]
        Tuple containing:
        - Set data dictionary (raw JSON for the set)
        - List of champion apiNames
        - Mapping of champion apiName to trait lists
        - Mapping of trait names to sorted breakpoint lists
        - Mapping of champion apiName to cost
        - Set of eligible trait names (2+ champions, has breakpoints, not blacklisted)
        - Mapping of trait names to frequency (how many champions have the trait)
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    blacklist = set(blacklist_traits) if blacklist_traits is not None else set()

    set_data = data["sets"][set_id]

    # Trait NAME -> sorted list of breakpoints (minUnits)
    trait_bps: Dict[str, List[int]] = {}
    for tr in set_data["traits"]:
        name = tr["name"]
        bps = sorted(e["minUnits"] for e in tr.get("effects", []) if e.get("minUnits") is not None)
        if bps:
            trait_bps[name] = bps

    # Known non-units inside champions
    EXCLUDE_API = {
        "TFT5_EmblemArmoryKey",
        "TFT_ArmoryKeyCompleted",
        "TFT_ArmoryKeyComponent",
        "TFT_ArmoryKeyOrnn",
        "TFT_ArmoryKeySupport",
        "TFT6_MercenaryChest",
    }

    # Legitimate units with atypical costs that should still be surfaced.
    INCLUDE_API = {
        "TFT16_AnnieTibbers",
    }

    champs: List[str] = []
    champ_traits: Dict[str, List[str]] = {}
    champ_cost: Dict[str, int] = {}

    for ch in set_data["champions"]:
        c_api = ch.get("apiName", "")

        # Remove fake entries
        if c_api in EXCLUDE_API:
            continue
        if ("ArmoryKey" in c_api) or ("MercenaryChest" in c_api):
            continue

        cost = ch.get("cost", None)
        if not isinstance(cost, int):
            continue

        # Optional heuristic: real units are normally 1-5 cost
        # If you later notice legit units outside 1-5, comment these out.
        if c_api not in INCLUDE_API and (cost < 1 or cost > 5):
            continue

        raw_traits = ch.get("traits", [])
        if not isinstance(raw_traits, list) or not raw_traits:
            continue

        # Keep champions even if all their traits are filtered out (e.g., traits
        # without breakpoints or blacklisted from eligibility). This lets
        # single-trait units like Ryze remain usable as carries/tanks even when
        # their traits contribute nothing to the Bronze objective.
        traits = [t for t in raw_traits if t in trait_bps]

        champs.append(c_api)
        champ_traits[c_api] = traits
        champ_cost[c_api] = cost

    # Detect "exclusive traits" (appear on only 1 champion)
    trait_freq = defaultdict(int)
    for c in champs:
        for t in set(champ_traits[c]):
            trait_freq[t] += 1

    # Eligible for Bronze for Life:
    # - appears on 2+ champs
    # - has breakpoints
    # - not blacklisted
    eligible_traits: Set[str] = {
        t for t, f in trait_freq.items() if f >= 2 and t in trait_bps and t not in blacklist
    }

    return set_data, champs, champ_traits, trait_bps, champ_cost, eligible_traits, dict(trait_freq)
