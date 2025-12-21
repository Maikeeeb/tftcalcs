from pathlib import Path
from typing import Dict, Set

PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent

JSON_PATH = REPO_ROOT / "en_us.json"
SET_ID = "16"
METATFT_TXT_PATH = REPO_ROOT / "metatft_units.txt"

TEAM_SIZE = 9
BEAM_WIDTH = 700  # bigger = better results, slower

# Traits that should NEVER count for Bronze for Life even if active.
BLACKLIST_TRAITS_BY_NAME: Set[str] = {
    "Targon",
}

# --- Emblem modeling (simple) ---
# If a trait is in EMBLEM_START_COUNTS, it starts at that many units (e.g., 1 emblem => +1).
EMBLEM_START_COUNTS: Dict[str, int] = {
    "Zaun": 1,
    "Ixtal": 1,
    "Freljord": 1,
    "Bilgewater": 1,
}

# If > 0, the optimizer will choose up to this many traits to receive +1 starting count (emblem),
# unless you hard-code EMBLEM_START_COUNTS above (hard-coded counts are always applied).
MAX_EMBLEMS_TOTAL = 0  # set 0 to disable automatic emblem selection

# Weights for unit strength tie-breaker. Higher = optimizer prefers "stronger" units among equally
# good bronze solutions.
W_WIN = 2.0  # win rate (0..1)
W_AVG = 1.0  # avg placement (lower is better)
W_FREQ = 0.1  # optional: popularity stability (0..1). keep small.
