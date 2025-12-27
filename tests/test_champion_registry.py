import json

import pytest

from bfl.champion_registry import list_playable_champions
from bfl.config import default_config
from bfl.config_loader import ConfigError, load_config


def test_list_playable_champions_reads_set_data():
    cfg = default_config()
    champs = list_playable_champions(cfg.json_path, cfg.set_id)

    assert "TFT16_Ashe" in champs
    assert len(champs) > 50


def test_load_config_validates_required_champions(tmp_path):
    cfg = default_config()
    invalid = tmp_path / "cfg.json"
    invalid.write_text(
        json.dumps(
            {
                "json_path": str(cfg.json_path),
                "set_id": cfg.set_id,
                "required_champions": {"NotAChamp": 1},
            }
        )
    )

    with pytest.raises(ConfigError):
        load_config(str(invalid))
