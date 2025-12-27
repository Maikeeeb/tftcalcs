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
REQUIRED_CHAMPIONS: Dict[str, int] = {
    "TFT16_Tristana": 0,
    "TFT16_Lulu": 0,
    "TFT16_Teemo": 0,
    "TFT16_Rumble": 0,
    "TFT16_Nautilus": 0,
    "TFT16_TwistedFate": 0,
    "TFT16_Gangplank": 0,
    "TFT16_Illaoi": 0,
    "TFT16_MissFortune": 0,
    "TFT16_Sion": 0,
    "TFT16_Briar": 0,
    "TFT16_Draven": 0,
    "TFT16_Ambessa": 0,
    "TFT16_Zoe": 0,
    "TFT16_Leona": 0,
    "TFT16_Aphelios": 0,
    "TFT16_Taric": 0,
    "TFT16_JarvanIV": 0,
    "TFT16_Sona": 0,
    "TFT16_Garen": 0,
    "TFT16_Lux": 0,
    "TFT16_Anivia": 0,
    "TFT16_Ashe": 0,
    "TFT16_Braum": 0,
    "TFT16_Lissandra": 0,
    "TFT16_Milio": 0,
    "TFT16_Neeko": 0,
    "TFT16_Jinx": 0,
    "TFT16_Caitlyn": 0,
    "TFT16_Vi": 0,
    "TFT16_Seraphine": 0,
    "TFT16_Yasuo": 0,
    "TFT16_Ahri": 0,
    "TFT16_Wukong": 0,
    "TFT16_Shen": 0,
    "TFT16_Malzahar": 0,
    "TFT16_RekSai": 0,
    "TFT16_ChoGath": 0,
    "TFT16_KogMaw": 0,
    "TFT16_Annie": 0,
    "TFT16_Ornn": 0,
    "TFT16_Kindred": 0,
    "TFT16_Azir": 0,
    "TFT16_Zilean": 0,
    "TFT16_Fiddlesticks": 0,
    "TFT16_Shyvana": 0,
    "TFT16_Galio": 0,
    "TFT16_TahmKench": 0,
    "TFT16_Sejuani": 0,
    "TFT16_Sett": 0,
    "TFT16_Brock": 0,
    "TFT16_THex": 0,
    "TFT16_BelVeth": 0,
    "TFT16_Singed": 0,
    "TFT16_AurelionSol": 0,
    "TFT16_Veigar": 0,
    "TFT16_BaronNashor": 0,
    "TFT16_Darius": 0,
    "TFT16_Yone": 0,
    "TFT16_Warwick": 0,
    "TFT16_Fizz": 0,
    "TFT16_Poppy": 0,
    "TFT16_Kennen": 0,
    "TFT16_Ziggs": 0,
    "TFT16_Aatrox": 0,
    "TFT16_Volibear": 0,
    "TFT16_Jhin": 0,
    "TFT16_Sylas": 0,
    "TFT16_Ryze": 0,
    "TFT16_Nidalee": 0,
    "TFT16_Tryndamere": 0,
    "TFT16_RiftHerald": 0,
    "TFT16_Mel": 0,
    "TFT16_Graves": 0,
    "TFT16_Skarner": 0,
    "TFT16_Diana": 0,
    "TFT16_Kaisa": 0,
    "TFT16_Renekton": 0,
    "TFT16_Nasus": 0,
    "TFT16_Xerath": 0,
    "TFT16_Thresh": 0,
    "TFT16_Gwen": 0,
    "TFT16_Kalista": 0,
    "TFT16_Leblanc": 0,
    "TFT16_Viego": 0,
    "TFT16_Ekko": 0,
    "TFT16_Bard": 0,
    "TFT16_Vayne": 0,
    "TFT16_Yunara": 0,
    "TFT16_Swain": 0,
    "TFT16_XinZhao": 0,
    "TFT16_Yorick": 0,
    "TFT16_Orianna": 0,
    "TFT16_Qiyana": 0,
    "TFT16_Loris": 0,
    "TFT16_Blitzcrank": 0,
    "TFT16_DrMundo": 0,
    "TFT16_Zaahen": 0,
    "TFT16_Lucian": 0,
    "TFT16_Kobuko": 0,
}

# Set value to N (>=1) to enforce a minimum final trait count (after emblems).
REQUIRED_TRAITS_MIN: Dict[str, int] = {
    # Only traits that appear on multiple champions
    "Arcanist": 0,
    "Bilgewater": 0,
    "Bruiser": 0,
    "Darkin": 0,
    "Defender": 0,
    "Demacia": 0,
    "Disruptor": 0,
    "Freljord": 0,
    "Gunslinger": 0,
    "Invoker": 0,
    "Ionia": 0,
    "Ixtal": 0,
    "Juggernaut": 0,
    "Longshot": 0,
    "Noxus": 0,
    "Piltover": 0,
    "Quickstriker": 0,
    "Shadow Isles": 0,
    "Shurima": 0,
    "Slayer": 0,
    "Targon": 0,
    "Vanquisher": 0,
    "Void": 0,
    "Warden": 0,
    "Yordle": 0,
    "Zaun": 0,
}

# Weights for unit strength tie-breaker. Higher = optimizer prefers "stronger" units among equally
# good bronze solutions.
W_WIN = 2.0  # win rate (0..1)
W_AVG = 1.0  # avg placement (lower is better)
W_FREQ = 0.1  # optional: popularity stability (0..1). keep small.
