import json
from dataclasses import replace

import pytest

from bfl.config import RYZE_API_NAME, default_config
from bfl.config_loader import ConfigError, load_config, validate_config_against_data
from bfl.set_loader import load_set_data


def test_load_config_merges_defaults_when_fields_missing(tmp_path):
    base = default_config()
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(
        json.dumps(
            {
                "team_size": 7,
                "blacklist_traits_by_name": ["Targon", "Bilgewater"],
                "emblem_start_counts": {"Zaun": 1},
                "w_win": 3.5,
            }
        )
    )

    cfg = load_config(str(cfg_path))

    assert cfg.team_size == 7
    assert cfg.beam_width == base.beam_width  # unchanged default
    assert cfg.blacklist_traits_by_name == {"Targon", "Bilgewater"}
    assert cfg.emblem_start_counts["Zaun"] == 1
    assert cfg.required_champions == base.required_champions
    assert cfg.required_traits_min == base.required_traits_min
    assert cfg.w_avg == base.w_avg
    assert cfg.w_win == 3.5


def test_load_config_rejects_non_iterable_blacklist(tmp_path):
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps({"blacklist_traits_by_name": "not-a-list"}))

    with pytest.raises(ConfigError):
        load_config(str(cfg_path))


def test_ryze_mode_defaults_to_required_ryze_and_level_9(tmp_path):
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(json.dumps({"mode": "ryze"}))

    cfg = load_config(str(cfg_path))

    assert cfg.team_size == 9
    assert cfg.required_champions[RYZE_API_NAME] == 1


def test_ryze_mode_respects_explicit_overrides(tmp_path):
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(
        json.dumps({"mode": "ryze", "team_size": 8, "required_champions": {RYZE_API_NAME: 0}})
    )

    cfg = load_config(str(cfg_path))

    assert cfg.team_size == 8
    assert cfg.required_champions[RYZE_API_NAME] == 0


def test_itemization_mode_accepts_item_inputs(tmp_path):
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(
        json.dumps(
            {
                "mode": "itemization",
                "available_components": ["B.F. Sword"],
                "available_completed_items": ["Infinity Edge"],
            }
        )
    )

    cfg = load_config(str(cfg_path))

    assert cfg.mode == "itemization"
    assert cfg.available_components == ["B.F. Sword"]
    assert cfg.available_completed_items == ["Infinity Edge"]


def test_itemization_mode_accepts_legacy_fields(tmp_path):
    cfg_path = tmp_path / "cfg.json"
    cfg_path.write_text(
        json.dumps(
            {
                "mode": "itemization",
                "itemization_components": ["B.F. Sword"],
                "itemization_completed_items": ["Infinity Edge"],
                "itemization_candidate_champions": ["TFT16_Jinx"],
            }
        )
    )

    cfg = load_config(str(cfg_path))

    assert cfg.available_components == ["B.F. Sword"]
    assert cfg.available_completed_items == ["Infinity Edge"]
    assert cfg.target_carries == ["TFT16_Jinx"]


def test_validate_config_against_data_flags_invalid_entries():
    base = default_config()
    _, champs, _, trait_bps, _, _, _ = load_set_data(base.json_path, base.set_id)

    invalid_traits = replace(
        base,
        required_traits_min={"NotATrait": 1},
    )
    with pytest.raises(ConfigError):
        validate_config_against_data(invalid_traits, champs, trait_bps)

    negative_emblems = replace(base, emblem_start_counts={"Zaun": -2})
    with pytest.raises(ConfigError):
        validate_config_against_data(negative_emblems, champs, trait_bps)

    zero_team_size = replace(base, team_size=0)
    with pytest.raises(ConfigError):
        validate_config_against_data(zero_team_size, champs, trait_bps)
