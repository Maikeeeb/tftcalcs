import sys
from pathlib import Path
import pytest

# Ensure the project root (tft calcs) is importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bfl.bronze_for_life import solve_beam_search_bronze_with_emblems


@pytest.fixture
def toy_set_data():
    return {
        "champions": [
            {"apiName": "TFT16_Alpha", "name": "Alpha", "characterName": "Alpha", "cost": 1, "traits": ["X", "Y"]},
            {"apiName": "TFT16_Beta",  "name": "Beta",  "characterName": "Beta",  "cost": 1, "traits": ["X", "Z"]},
            {"apiName": "TFT16_Gamma", "name": "Gamma", "characterName": "Gamma", "cost": 1, "traits": ["Y", "Z"]},
            {"apiName": "TFT16_Delta", "name": "Delta", "characterName": "Delta", "cost": 1, "traits": ["W"]},  # exclusive
        ],
        "traits": [
            {"name": "X", "effects": [{"minUnits": 2}, {"minUnits": 4}]},
            {"name": "Y", "effects": [{"minUnits": 2}]},
            {"name": "Z", "effects": [{"minUnits": 2}]},
            {"name": "W", "effects": [{"minUnits": 1}]},
            {"name": "Targon", "effects": [{"minUnits": 1}]},
        ],
    }


@pytest.fixture
def result_from_beam_search(toy_set_data):
    champs = [c["apiName"] for c in toy_set_data["champions"]]
    champ_traits = {c["apiName"]: c["traits"] for c in toy_set_data["champions"]}
    trait_bps = {t["name"]: sorted(e["minUnits"] for e in t["effects"]) for t in toy_set_data["traits"]}
    eligible = {"X", "Y", "Z"}
    power_map = {c: 0.0 for c in champs}

    team, *_ = solve_beam_search_bronze_with_emblems(
        champs=champs,
        champ_traits=champ_traits,
        trait_bps=trait_bps,
        eligible_traits=eligible,
        team_size=2,
        beam_width=50,
        hard_emblems={},
        max_emblems_total=0,
        power_map=power_map,
        required_champions=None,
        required_traits_min=None,
    )
    return team
