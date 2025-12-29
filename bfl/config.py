from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Set

PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent
UNLOCKABLE_CHAMPIONS_PATH = REPO_ROOT / "frontend" / "src" / "data" / "unlockable_champions.json"
UNLOCKABLE_CHAMPIONS = tuple(json.loads(UNLOCKABLE_CHAMPIONS_PATH.read_text(encoding="utf-8")))


# Traits that should NEVER count for Bronze for Life even if active.
DEFAULT_BLACKLIST_TRAITS_BY_NAME: Set[str] = {
    "Targon",
}

# --- Emblem modeling (simple) ---
# If a trait is in EMBLEM_START_COUNTS, it starts at that many units (e.g., 1 emblem => +1).
DEFAULT_EMBLEM_START_COUNTS: Dict[str, int] = {
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
    "Shurima": 0,
    "Slayer": 0,
    "Targon": 0,
    "Vanquisher": 0,
    "Void": 0,
    "Warden": 0,
    "Yordle": 0,
    "Zaun": 0,
}

DEFAULT_REQUIRED_CHAMPIONS: Dict[str, int] = {
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
    "TFT16_AnnieTibbers": 0,
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

for unlockable in UNLOCKABLE_CHAMPIONS:
    if unlockable not in DEFAULT_REQUIRED_CHAMPIONS:
        raise ValueError(f"Unlockable champion not found in defaults: {unlockable}")
    DEFAULT_REQUIRED_CHAMPIONS[unlockable] = -1

# Set value to N (>=1) to enforce a minimum final trait count (after emblems).
DEFAULT_REQUIRED_TRAITS_MIN: Dict[str, int] = {
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


@dataclass
class Config:
    json_path: Path
    set_id: str
    metatft_txt_path: Path
    metatft_traits_path: Path
    team_size: int
    beam_width: int
    blacklist_traits_by_name: Set[str] = field(default_factory=set)
    emblem_start_counts: Dict[str, int] = field(default_factory=dict)
    max_emblems_total: int = 0
    required_champions: Dict[str, int] = field(default_factory=dict)
    required_traits_min: Dict[str, int] = field(default_factory=dict)
    w_win: float = 2.0
    w_avg: float = 1.0
    w_freq: float = 0.1
    mode: str = "bronze"
    must_have_itemized_tank: bool = True
    seed_verticals: bool = True

    def to_dict(self) -> Dict:
        return {
            "json_path": str(self.json_path),
            "set_id": self.set_id,
            "metatft_txt_path": str(self.metatft_txt_path),
            "metatft_traits_path": str(self.metatft_traits_path),
            "team_size": self.team_size,
            "beam_width": self.beam_width,
            "blacklist_traits_by_name": sorted(self.blacklist_traits_by_name),
            "emblem_start_counts": dict(self.emblem_start_counts),
            "max_emblems_total": self.max_emblems_total,
            "required_champions": dict(self.required_champions),
            "required_traits_min": dict(self.required_traits_min),
            "w_win": self.w_win,
            "w_avg": self.w_avg,
            "w_freq": self.w_freq,
            "mode": self.mode,
            "must_have_itemized_tank": self.must_have_itemized_tank,
            "seed_verticals": self.seed_verticals,
        }


def default_config() -> Config:
    return Config(
        json_path=REPO_ROOT / "en_us.json",
        set_id="16",
        metatft_txt_path=REPO_ROOT / "metatft_units.txt",
        metatft_traits_path=REPO_ROOT / "metatft_traits.txt",
        team_size=9,
        beam_width=700,
        blacklist_traits_by_name=set(DEFAULT_BLACKLIST_TRAITS_BY_NAME),
        emblem_start_counts=dict(DEFAULT_EMBLEM_START_COUNTS),
        max_emblems_total=0,
        required_champions=dict(DEFAULT_REQUIRED_CHAMPIONS),
        required_traits_min=dict(DEFAULT_REQUIRED_TRAITS_MIN),
        w_win=2.0,
        w_avg=1.0,
        w_freq=0.1,
        mode="bronze",
        must_have_itemized_tank=True,
        seed_verticals=True,
    )
