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
    # Origins
    "Zaun": 0,
    "Piltover": 0,
    "Bilgewater": 0,
    "Freljord": 0,
    "Ixtal": 0,
    "Void": 0,
    "Darkin": 0,

    # Classes
    "Arcanist": 0,
    "Bruiser": 0,
    "Defender": 0,
    "Invoker": 0,
    "Juggernaut": 0,
    "Longshot": 0,
    "Slayer": 0,
    "Vanquisher": 0,
    "Warden": 0,
    "Yordle": 0,

    # Add/remove based on what your JSON actually allows
}

# If > 0, the optimizer will choose up to this many traits to receive +1 starting count (emblem),
# unless you hard-code EMBLEM_START_COUNTS above (hard-coded counts are always applied).
MAX_EMBLEMS_TOTAL = 0  # set 0 to disable automatic emblem selection

# Required constraints (complete templates generated at runtime if left empty)
# Set value to 1 to force a champion into the team.
REQUIRED_CHAMPIONS: Dict[str, int] = {}

# Set value to N (>=1) to enforce a minimum final trait count (after emblems).
REQUIRED_TRAITS_MIN: Dict[str, int] = {}

# Weights for unit strength tie-breaker. Higher = optimizer prefers "stronger" units among equally
# good bronze solutions.
W_WIN = 2.0  # win rate (0..1)
W_AVG = 1.0  # avg placement (lower is better)
W_FREQ = 0.1  # optional: popularity stability (0..1). keep small.
