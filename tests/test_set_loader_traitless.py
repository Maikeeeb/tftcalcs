import json
from pathlib import Path

from bfl.set_loader import load_set_data


def test_traitless_champion_is_kept(tmp_path: Path):
    data = {
        "sets": {
            "16": {
                "traits": [
                    # Trait exists but has no breakpoints (minUnits missing)
                    {"name": "Singular", "effects": [{"maxUnits": 1}]},
                ],
                "champions": [
                    {
                        "apiName": "TFT16_RyzeClone",
                        "cost": 4,
                        # All traits will be filtered out by load_set_data
                        "traits": ["Singular"],
                    }
                ],
            }
        }
    }

    path = tmp_path / "set.json"
    path.write_text(json.dumps(data))

    _, champs, champ_traits, trait_bps, champ_cost, eligible_traits, trait_freq = load_set_data(
        str(path), "16"
    )

    assert champs == ["TFT16_RyzeClone"]
    assert champ_traits["TFT16_RyzeClone"] == []
    assert champ_cost["TFT16_RyzeClone"] == 4
    assert trait_bps == {}
    assert eligible_traits == set()
    assert trait_freq == {}
