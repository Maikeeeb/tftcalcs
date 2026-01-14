import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Set


def normalize_name(s: str) -> str:
    """Normalize a string for matching by removing spaces and punctuation.

    Converts to lowercase and removes all non-alphanumeric characters to
    enable fuzzy matching of names.

    Parameters
    ----------
    s : str
        String to normalize.

    Returns
    -------
    str
        Normalized string (lowercase, alphanumeric only).
    """
    return re.sub(r"[^a-z0-9]+", "", s.lower())


TANK_ITEM_NAMES: Set[str] = {
    normalize_name(name)
    for name in [
        "sunfire cape",
        "warmogs",
        "gargoyles",
        "spirit visage",
        "evenshroud",
        "protector's vow",
        "protectors vow",
        "bramble vest",
        "dragon claw",
        "adaptive helm",
        "steadfast heart",
        "ionic spark",
    ]
}


def _count_tank_items(items: Iterable[str] | None) -> int:
    return sum(1 for item in items or [] if normalize_name(item) in TANK_ITEM_NAMES)


def is_tank_item_build(items: Iterable[str] | None) -> bool:
    """Check if an item build is primarily tank-focused.

    A build is considered tank-focused if at least half of the items
    (rounded up) are tank items.

    Parameters
    ----------
    items : Iterable[str] | None
        List of item names to check.

    Returns
    -------
    bool
        True if the build is primarily tank items, False otherwise.
    """
    items = list(items or [])
    if not items:
        return False
    return _count_tank_items(items) >= (len(items) + 1) // 2


def classify_tank_champions(
    unit_stats: Dict[str, Dict[str, float | List[str]]],
    champ_cost: Dict[str, int] | None = None,
) -> Set[str]:
    """Return champions whose popular items are primarily tank items and cost 4+."""

    tanks: Set[str] = set()
    for champ, stats in unit_stats.items():
        items = stats.get("items")
        if not isinstance(items, list):
            continue

        if champ_cost is not None:
            cost = champ_cost.get(champ)
            if cost is None or cost < 4:
                continue

        if is_tank_item_build(items):
            tanks.add(champ)
    return tanks


@dataclass(frozen=True)
class TraitStat:
    """Represents a MetaTFT trait breakpoint with performance stats."""

    required: int
    tier: str
    avg: float
    win: float
    freq: float


def best_trait_stat(
    trait: str, count: int, trait_stats: Dict[str, List[TraitStat]]
) -> TraitStat | None:
    """Return the strongest MetaTFT breakpoint satisfied for ``trait``.

    Used for surfacing the most relevant MetaTFT values for a trait given the
    current team count.
    """

    stats = trait_stats.get(trait)
    if not stats:
        return None

    eligible = [s for s in stats if count >= s.required]
    if not eligible:
        return None

    return max(eligible, key=lambda s: s.required)


def parse_metatft_units(text: str) -> Dict[str, Dict[str, float | List[str]]]:
    """Parse MetaTFT unit paste data into a structured dictionary.

    Parses the MetaTFT unit table copy-paste format and extracts unit stats
    including average placement, win rate, frequency, tier, and popular items.

    Parameters
    ----------
    text : str
        Raw MetaTFT unit paste text.

    Returns
    -------
    Dict[str, Dict[str, float | List[str]]]
        Dictionary mapping unit names to their stats. Each unit dict contains:
        - "avg": average placement (float)
        - "win": win rate (float, 0-1)
        - "freq": play frequency (float, 0-1)
        - "tier": tier letter (str)
        - "items": list of popular item names (List[str])
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out: Dict[str, Dict[str, float | List[str]]] = {}

    tier_set = {"S", "A", "B", "C", "D"}

    def is_float(s: str) -> bool:
        return re.fullmatch(r"\d+(\.\d+)?", s) is not None

    def parse_percent(s: str) -> float:
        return float(s.replace("%", "").strip()) / 100.0

    # Heuristic: ignore these known non-unit labels / columns
    headers = {"Unit", "Tier", "Avg Place", "Win Rate", "Frequency", "Popular Items"}

    for idx, ln in enumerate(lines):
        if ln in headers or ln not in tier_set:
            continue

        # Walk backward to find the closest preceding candidate name
        name = None
        name_idx = idx - 1
        while name_idx >= 0:
            candidate = lines[name_idx]

            if candidate.startswith("Unlockable Unit"):
                name = candidate.replace("Unlockable Unit", "").strip()
                break

            if candidate in headers or candidate in tier_set:
                name_idx -= 1
                continue

            if re.fullmatch(r"[0-9.,% ]+%?", candidate):
                name_idx -= 1
                continue

            name = candidate
            break

        if name is None:
            continue

        # Try to use an immediate repeat of the name (MetaTFT often echoes it)
        if name_idx + 1 < len(lines):
            repeat = lines[name_idx + 1]
            if (
                repeat not in headers
                and repeat not in tier_set
                and not repeat.startswith("Unlockable Unit")
                and not re.fullmatch(r"[0-9.,% ]+%?", repeat)
                and normalize_name(repeat) == normalize_name(name)
            ):
                name = repeat

        # Stats follow the tier row in a fixed order
        if idx + 3 >= len(lines):
            continue

        avg_line = lines[idx + 1]
        win_line = lines[idx + 2]
        freq_line = lines[idx + 3]

        if not is_float(avg_line):
            continue

        if not re.fullmatch(r"\d+(\.\d+)?\s*%", win_line):
            continue

        freq_match = re.search(r"([0-9]+(\.[0-9]+)?)\s*%$", freq_line)
        if not freq_match:
            continue

        avg = float(avg_line)
        win = parse_percent(win_line)
        freq = float(freq_match.group(1)) / 100.0

        # Item rows extend until the next tier/header/unlockable/numeric line
        items: List[str] = []
        item_idx = idx + 4
        while item_idx < len(lines):
            nxt = lines[item_idx]

            if nxt in headers or nxt in tier_set:
                break

            if nxt.startswith("Unlockable Unit"):
                break

            if re.fullmatch(r"[0-9.,% ]+%?", nxt):
                break

            items.append(nxt)
            item_idx += 1

        out[name] = {"avg": avg, "win": win, "freq": freq, "items": items}

    return out


def build_name_to_api_map(set_data) -> Dict[str, str]:
    """Build mapping from normalized display name to apiName.

    Creates a mapping that allows fuzzy matching of unit names to their
    apiName identifiers. Tries multiple name fields: 'name', 'characterName',
    and the tail of the apiName (e.g., "Aatrox" from "TFT16_Aatrox").

    Parameters
    ----------
    set_data : dict
        Set data dictionary from en_us.json containing champions list.

    Returns
    -------
    Dict[str, str]
        Mapping from normalized display names to champion apiNames.
    """
    m: Dict[str, str] = {}
    for ch in set_data["champions"]:
        api = ch.get("apiName", "")

        display_candidates = [
            ch.get("name", ""),
            ch.get("characterName", ""),
        ]

        # "TFT16_Aatrox" -> "Aatrox"
        if "_" in api:
            display_candidates.append(api.split("_", 1)[1])

        for disp in display_candidates:
            if disp:
                m[normalize_name(disp)] = api
    return m


def metatft_to_unit_stats(paste: str, set_data) -> Dict[str, Dict[str, float | List[str]]]:
    """Convert MetaTFT unit paste to dictionary keyed by champion apiName.

    Parses the MetaTFT paste and maps unit names to their apiName identifiers
    using set data. Filters out items that match champion names to avoid
    confusion.

    Parameters
    ----------
    paste : str
        Raw MetaTFT unit paste text.
    set_data : dict
        Set data dictionary from en_us.json.

    Returns
    -------
    Dict[str, Dict[str, float | List[str]]]
        Dictionary mapping champion apiNames to their stats. Each entry
        contains "avg", "win", "freq", "tier", and "items" keys.
    """
    paste = paste.strip()
    if not paste:
        return {}

    raw = parse_metatft_units(paste)
    name_to_api = build_name_to_api_map(set_data)
    champion_keys = set(name_to_api)

    unit_stats: Dict[str, Dict[str, float | List[str]]] = {}
    missed: List[str] = []

    for name, stats in raw.items():
        api = name_to_api.get(normalize_name(name))
        if not api:
            missed.append(name)
            continue
        items_value = stats.get("items", [])
        items_list = items_value if isinstance(items_value, list) else []
        filtered_items = [item for item in items_list if normalize_name(item) not in champion_keys]
        unit_stats[api] = {**stats, "items": filtered_items}

    if missed:
        print(
            f"Warning: couldn't map {len(missed)} units from MetaTFT paste (first 15): {missed[:15]}"
        )

    print(f"Loaded MetaTFT stats for {len(unit_stats)} units.")
    return unit_stats


NEUTRAL_AVG_PLACEMENT = 4.5
PESSIMISM_SPREAD = 0.3


def pessimistic_avg(avg: float, freq: float) -> float:
    """Return a conservative average placement using 1 stdev of pessimism.

    MetaTFT only provides an average placement and a play-rate frequency. Treat
    the frequency as a crude proxy for confidence: higher frequency narrows the
    possible range, while low frequency widens it. We model this by adding up to
    ``PESSIMISM_SPREAD`` placements of pessimism when frequency is near zero and
    tapering the pessimism to zero as frequency approaches one.
    """

    freq = max(0.0, min(1.0, freq))
    return avg + (1.0 - freq) * PESSIMISM_SPREAD


def unit_power(
    api: str,
    unit_stats: Dict[str, Dict[str, float]],
    w_win: float = 2.0,
    w_avg: float = 1.0,
    w_freq: float = 0.1,
) -> float:
    """Calculate power score for a unit.

    Returns a weighted score combining win rate, average placement, and
    play frequency. Higher scores indicate stronger unit performance.
    Bigger is better.

    Parameters
    ----------
    api : str
        Champion apiName to score.
    unit_stats : Dict[str, Dict[str, float]]
        Dictionary mapping champion apiNames to their stats (avg, win, freq).
    w_win : float, optional
        Weight for win rate (default: 2.0).
    w_avg : float, optional
        Weight for average placement (default: 1.0).
    w_freq : float, optional
        Weight for play frequency (default: 0.1).

    Returns
    -------
    float
        Power score for the unit. Returns 0.0 if unit not found in stats.
    """
    s = unit_stats.get(api)
    if not s:
        return 0.0
    win = float(s.get("win", 0.0))  # 0..1
    avg = float(s.get("avg", NEUTRAL_AVG_PLACEMENT))  # ~2..8 (lower better)
    freq = float(s.get("freq", 0.0))  # 0..1
    adj_avg = pessimistic_avg(avg, freq)
    return (w_win * win) + (w_freq * freq) - (w_avg * (adj_avg - NEUTRAL_AVG_PLACEMENT))


def load_metatft_txt(path: str) -> str:
    """Load MetaTFT paste text from a file.

    Parameters
    ----------
    path : str
        Path to the MetaTFT paste file.

    Returns
    -------
    str
        File contents as a string. Returns empty string if file not found.
    """
    from bfl.io_utils import retry_file_operation

    @retry_file_operation(retryable_exceptions=(IOError, OSError, PermissionError))
    def _load_file():
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    try:
        return _load_file()
    except FileNotFoundError:
        print(f"MetaTFT file not found: {path}")
        return ""


def parse_metatft_traits(text: str) -> Dict[str, List[TraitStat]]:
    """
    Parse a MetaTFT trait paste into a mapping of trait name -> breakpoints.

    The input is expected to resemble the MetaTFT trait table copy-paste. Rows
    generally look like::

        traitBase
        Shurima
        4 Shurima
        S
        1.07
        94.6%
        28,972 0.1%

    This parser is intentionally forgiving and skips entries that do not match
    the expected pattern.
    """

    tokens = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out: Dict[str, List[TraitStat]] = {}

    def _parse_required(label: str) -> int | None:
        m = re.match(r"(\d+)", label)
        return int(m.group(1)) if m else None

    def _parse_percent(value: str) -> float:
        return float(value.replace("%", "").replace(",", "").strip()) / 100.0

    i = 0
    while i < len(tokens):
        if tokens[i] != "traitBase":
            i += 1
            continue

        if i + 6 >= len(tokens):
            break

        trait_name = tokens[i + 1]
        label = tokens[i + 2]
        tier = tokens[i + 3]
        avg_str = tokens[i + 4]
        win_str = tokens[i + 5]
        freq_line = tokens[i + 6]

        required = _parse_required(label)
        if required is None:
            i += 1
            continue

        try:
            avg = float(avg_str)
            win = _parse_percent(win_str)
        except ValueError:
            i += 1
            continue

        freq_match = re.search(r"([0-9]+(?:\.[0-9]+)?)%$", freq_line.replace(",", ""))
        freq = float(freq_match.group(1)) / 100.0 if freq_match else 0.0

        out.setdefault(trait_name, []).append(
            TraitStat(required=required, tier=tier, avg=avg, win=win, freq=freq)
        )

        i += 7

    # Sort breakpoints from lowest to highest requirement for easy lookup.
    for trait, stats in out.items():
        out[trait] = sorted(stats, key=lambda s: s.required)

    return out


def metatft_to_trait_stats(paste: str, set_data) -> Dict[str, List[TraitStat]]:
    """Convert MetaTFT trait paste to dictionary keyed by trait name.

    Parses the MetaTFT trait paste and maps trait names to their identifiers
    as they appear in set data. Unknown traits are ignored.

    Parameters
    ----------
    paste : str
        Raw MetaTFT trait paste text.
    set_data : dict
        Set data dictionary from en_us.json.

    Returns
    -------
    Dict[str, List[TraitStat]]
        Dictionary mapping trait names to lists of TraitStat objects,
        sorted by required count (lowest to highest).
    """

    paste = paste.strip()
    if not paste:
        return {}

    raw = parse_metatft_traits(paste)
    name_to_trait = {normalize_name(tr["name"]): tr["name"] for tr in set_data["traits"]}

    trait_stats: Dict[str, List[TraitStat]] = {}
    missed: List[str] = []

    for name, stats in raw.items():
        key = name_to_trait.get(normalize_name(name))
        if not key:
            missed.append(name)
            continue
        trait_stats[key] = stats

    if missed:
        print(
            f"Warning: couldn't map {len(missed)} traits from MetaTFT paste (first 15): {missed[:15]}"
        )

    print(f"Loaded MetaTFT stats for {len(trait_stats)} traits.")
    return trait_stats


def trait_power(
    trait: str,
    count: int,
    trait_stats: Dict[str, List[TraitStat]],
    w_win: float = 2.0,
    w_avg: float = 1.0,
    w_freq: float = 0.1,
) -> float:
    """Calculate power score for a trait at the given count.

    Returns a weighted score based on the highest breakpoint satisfied for
    the trait. Higher scores indicate stronger trait performance.

    Parameters
    ----------
    trait : str
        Trait name to score.
    count : int
        Current trait count on the team.
    trait_stats : Dict[str, List[TraitStat]]
        Dictionary mapping trait names to their breakpoint stats.
    w_win : float, optional
        Weight for win rate (default: 2.0).
    w_avg : float, optional
        Weight for average placement (default: 1.0).
    w_freq : float, optional
        Weight for play frequency (default: 0.1).

    Returns
    -------
    float
        Power score for the trait. Returns 0.0 if trait not found or
        no breakpoint satisfied.
    """

    stats = trait_stats.get(trait)
    if not stats:
        return 0.0

    eligible = [s for s in stats if count >= s.required]
    if not eligible:
        return 0.0

    best = max(eligible, key=lambda s: s.required)
    adj_avg = pessimistic_avg(best.avg, best.freq)
    score = (w_win * best.win) + (w_freq * best.freq) - (w_avg * (adj_avg - NEUTRAL_AVG_PLACEMENT))

    return score
