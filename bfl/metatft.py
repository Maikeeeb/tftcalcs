import re
from typing import Dict, List


def normalize_name(s: str) -> str:
    # Lowercase, remove spaces/punctuation for matching
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def parse_metatft_units(text: str) -> Dict[str, Dict[str, float]]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out: Dict[str, Dict[str, float]] = {}

    tier_set = {"S", "A", "B", "C", "D"}

    def is_float(s: str) -> bool:
        return re.fullmatch(r"\d+(\.\d+)?", s) is not None

    def parse_percent(s: str) -> float:
        return float(s.replace("%", "").strip()) / 100.0

    # Heuristic: ignore these known non-unit labels / columns
    headers = {"Unit", "Tier", "Avg Place", "Win Rate", "Frequency", "Popular Items"}

    # Heuristic: items are usually followed by more items; we’ll skip candidate names
    # unless they are followed soon by a valid tier/avg/win trio.
    i = 0
    while i < len(lines):
        ln = lines[i]

        if ln in headers:
            i += 1
            continue

        # Strip "Unlockable Unit" prefix if present (sometimes glued)
        if ln.startswith("Unlockable Unit"):
            ln = ln.replace("Unlockable Unit", "").strip()

        # Candidate name must not be a tier and must not be numeric-ish
        if ln and ln not in tier_set and not re.fullmatch(r"[0-9.,%]+", ln):
            name = ln

            # Search forward for a *tight* pattern: tier, avg, win%, freq%
            tier = None
            avg = None
            win = None
            freq = 0.0
            found = False

            for j in range(i + 1, min(i + 7, len(lines))):
                x = lines[j]

                if x in headers:
                    # if we hit headers, stop scanning this candidate
                    break

                if tier is None:
                    if x in tier_set:
                        tier = x
                    continue

                if avg is None:
                    if is_float(x):
                        avg = float(x)
                    continue

                if win is None:
                    # win rate like "13.6%"
                    if re.fullmatch(r"\d+(\.\d+)?\s*%", x):
                        win = parse_percent(x)
                    continue

                # freq line: ends with percent, often has a count before it
                m = re.search(r"([0-9]+(\.[0-9]+)?)\s*%$", x)
                if m:
                    freq = float(m.group(1)) / 100.0
                found = True
                break

            # Only accept if it really looks like a unit row
            if found and tier is not None and avg is not None and win is not None:
                out[name] = {"avg": avg, "win": win, "freq": freq}

        i += 1

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


def metatft_to_unit_stats(paste: str, set_data) -> Dict[str, Dict[str, float]]:
    """
    Converts the MetaTFT paste into a dict keyed by apiName:
      { "TFT16_Aatrox": {"avg":..., "win":..., "freq":...}, ... }
    """
    paste = paste.strip()
    if not paste:
        return {}

    raw = parse_metatft_units(paste)
    name_to_api = build_name_to_api_map(set_data)

    unit_stats: Dict[str, Dict[str, float]] = {}
    missed: List[str] = []

    for name, stats in raw.items():
        api = name_to_api.get(normalize_name(name))
        if not api:
            missed.append(name)
            continue
        unit_stats[api] = stats

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
