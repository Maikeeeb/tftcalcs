import sys
from pathlib import Path
import pytest

# Ensure the project root (tft calcs) is importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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

