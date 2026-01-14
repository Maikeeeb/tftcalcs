from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Set

PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent
UNLOCKABLE_CHAMPIONS_PATH = REPO_ROOT / "frontend" / "src" / "data" / "unlockable_champions.json"
UNLOCKABLE_CHAMPIONS = tuple(json.loads(UNLOCKABLE_CHAMPIONS_PATH.read_text(encoding="utf-8")))
RYZE_API_NAME = "TFT16_Ryze"


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


def _generate_default_required_champions() -> Dict[str, int]:
    """Generate default required champions dict from en_us.json."""
    # Import here to avoid circular import (champion_registry depends on config)
    from bfl.set_loader import load_set_data

    # Use default paths - same as default_config uses
    json_path = REPO_ROOT / "data" / "en_us.json"
    set_id = "16"

    _, champions, *_ = load_set_data(json_path, set_id)
    result = {champ: 0 for champ in champions}

    # Apply unlockable logic
    for unlockable in UNLOCKABLE_CHAMPIONS:
        if unlockable not in result:
            raise ValueError(f"Unlockable champion not found in champions: {unlockable}")
        result[unlockable] = -1

    return result


DEFAULT_REQUIRED_CHAMPIONS: Dict[str, int] = _generate_default_required_champions()

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
    """Configuration for the Bronze for Life solver.

    Attributes
    ----------
    json_path : Path
        Path to the Riot set data JSON file (e.g., en_us.json).
    set_id : str
        Set identifier within the JSON file (e.g., "16" for Set 16).
    metatft_txt_path : Path
        Path to MetaTFT unit stats paste file.
    metatft_traits_path : Path
        Path to MetaTFT trait stats paste file.
    team_size : int
        Maximum number of unit slots on the team.
    beam_width : int
        Width of the beam search (number of states to keep per iteration).
    blacklist_traits_by_name : Set[str]
        Traits that should never count for Bronze for Life even if active.
    emblem_start_counts : Dict[str, int]
        Fixed emblem counts per trait (e.g., {"Zaun": 1} means +1 Zaun from emblems).
    max_emblems_total : int
        Maximum number of additional emblems the solver can auto-assign.
    required_champions : Dict[str, int]
        Champion requirements: 1 = required, -1 = banned, 0 = no constraint.
    required_traits_min : Dict[str, int]
        Minimum trait counts required (after emblems are applied).
    w_win : float
        Weight for win rate in MetaTFT power calculations.
    w_avg : float
        Weight for average placement in MetaTFT power calculations.
    w_freq : float
        Weight for frequency/play rate in MetaTFT power calculations.
    mode : str
        Solver mode: "bronze", "standard", "ryze", or "itemization".
    must_have_itemized_tank : bool
        Whether the team must include at least one tank champion (cost 4+ with tank items).
    seed_verticals : bool
        Whether to seed beam search with vertical-focused teams.
    available_components : list[str]
        Available component items for itemization mode (by name or apiName).
    available_completed_items : list[str]
        Available completed items for itemization mode (by name or apiName).
    target_carries : list[str]
        Champion apiNames to rank in itemization mode (empty = all eligible carries).
    team_traits : list[str]
        Traits already active on the team (tie-breaker for itemization).
    needed_traits : list[str]
        Traits to add or reinforce (tie-breaker for itemization).
    allow_reforge : bool
        Whether completed items can count as reforged into another item for scoring.
    """

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
    available_components: list[str] = field(default_factory=list)
    available_completed_items: list[str] = field(default_factory=list)
    target_carries: list[str] = field(default_factory=list)
    team_traits: list[str] = field(default_factory=list)
    needed_traits: list[str] = field(default_factory=list)
    allow_reforge: bool = False

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
            "available_components": list(self.available_components),
            "available_completed_items": list(self.available_completed_items),
            "target_carries": list(self.target_carries),
            "team_traits": list(self.team_traits),
            "needed_traits": list(self.needed_traits),
            "allow_reforge": self.allow_reforge,
        }


def default_config() -> Config:
    """Return a Config instance with default values.

    Returns
    -------
    Config
        Configuration object with default paths, team size 9, beam width 700,
        bronze mode, and default MetaTFT weights.
    """
    return Config(
        json_path=REPO_ROOT / "data" / "en_us.json",
        set_id="16",
        metatft_txt_path=REPO_ROOT / "data" / "metatft_units.txt",
        metatft_traits_path=REPO_ROOT / "data" / "metatft_traits.txt",
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
        available_components=[],
        available_completed_items=[],
        target_carries=[],
        team_traits=[],
        needed_traits=[],
        allow_reforge=False,
    )
