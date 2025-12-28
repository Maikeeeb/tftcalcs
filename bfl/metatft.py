import re
from dataclasses import dataclass
from typing import Dict, List


def normalize_name(s: str) -> str:
    # Lowercase, remove spaces/punctuation for matching
    return re.sub(r"[^a-z0-9]+", "", s.lower())


@dataclass(frozen=True)
class TraitStat:
    """Represents a MetaTFT trait breakpoint with performance stats."""

    required: int
    tier: str
    avg: float
    win: float
    freq: float


def parse_metatft_units(text: str) -> Dict[str, Dict[str, float | List[str]]]:
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
    """
    Builds mapping from normalized display name -> apiName using your en_us.json set data.
    Tries 'name', 'characterName', and apiName tail.
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
    """
    Converts the MetaTFT paste into a dict keyed by apiName:
      { "TFT16_Aatrox": {"avg":..., "win":..., "freq":...}, ... }
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
        filtered_items = [
            item for item in stats.get("items", []) if normalize_name(item) not in champion_keys
        ]
        unit_stats[api] = {**stats, "items": filtered_items}

    if missed:
        print(f"Warning: couldn't map {len(missed)} units from MetaTFT paste (first 15): {missed[:15]}")

    print(f"Loaded MetaTFT stats for {len(unit_stats)} units.")
    return unit_stats


def unit_power(
    api: str,
    unit_stats: Dict[str, Dict[str, float]],
    w_win: float = 2.0,
    w_avg: float = 1.0,
    w_freq: float = 0.1,
) -> float:
    """
    Bigger is better.
    """
    s = unit_stats.get(api)
    if not s:
        return 0.0
    win = float(s.get("win", 0.0))  # 0..1
    avg = float(s.get("avg", 4.5))  # ~2..8 (lower better)
    freq = float(s.get("freq", 0.0))  # 0..1
    return (w_win * win) - (w_avg * avg) + (w_freq * freq)


def load_metatft_txt(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
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
    """
    Converts the MetaTFT trait paste into a dict keyed by trait name as it
    appears in the set data. Unknown traits are ignored.
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
    """
    Returns a score for the highest breakpoint satisfied for ``trait``.
    """

    stats = trait_stats.get(trait)
    if not stats:
        return 0.0

    eligible = [s for s in stats if count >= s.required]
    if not eligible:
        return 0.0

    best = max(eligible, key=lambda s: s.required)
    score = (w_win * best.win) - (w_avg * best.avg) + (w_freq * best.freq)

    # MetaTFT averages are lower-better, so some breakpoints can produce
    # negative values when directly combined with the weights. Returning
    # zero instead of the raw negative score prevents the solver from
    # treating active traits as a penalty relative to having no traits at
    # all, which keeps standard mode focused on activating the strongest
    # available traits.
    return max(0.0, score)
