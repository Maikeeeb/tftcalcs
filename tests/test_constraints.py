import pytest

from bfl.bronze_for_life import solve_beam_search_bronze_with_emblems
from bfl.set_loader import load_set_data
from bfl.config import default_config


def _build_inputs(toy_set_data):
    champs = [c["apiName"] for c in toy_set_data["champions"]]
    champ_traits = {c["apiName"]: c["traits"] for c in toy_set_data["champions"]}
    trait_bps = {
        t["name"]: sorted(e["minUnits"] for e in t["effects"]) for t in toy_set_data["traits"]
    }
    eligible = {"X", "Y", "Z"}
    power_map = {c: 0.0 for c in champs}
    return champs, champ_traits, trait_bps, eligible, power_map


def test_required_champion_forced_into_team(toy_set_data):
    champs, champ_traits, trait_bps, eligible, power_map = _build_inputs(toy_set_data)

    team, *_ = solve_beam_search_bronze_with_emblems(
        champs=champs,
        champ_traits=champ_traits,
        trait_bps=trait_bps,
        eligible_traits=eligible,
        team_size=2,
        beam_width=10,
        hard_emblems={},
        max_emblems_total=0,
        power_map=power_map,
        required_champions={"TFT16_Gamma": 1},
        required_traits_min=None,
    )

    assert "TFT16_Gamma" in team


def test_required_trait_minimum_respected(toy_set_data):
    champs, champ_traits, trait_bps, eligible, power_map = _build_inputs(toy_set_data)

    (
        _team,
        _emblems,
        _power,
        _bronze,
        counts,
        _bronze_traits,
        _active_traits,
        _upgraded_traits,
        _used_traits,
    ) = solve_beam_search_bronze_with_emblems(
        champs=champs,
        champ_traits=champ_traits,
        trait_bps=trait_bps,
        eligible_traits=eligible,
        team_size=2,
        beam_width=10,
        hard_emblems={},
        max_emblems_total=0,
        power_map=power_map,
        required_champions=None,
        required_traits_min={"Y": 2},
    )

    assert counts.get("Y", 0) >= 2


def test_impossible_required_trait_raises(toy_set_data):
    champs, champ_traits, trait_bps, eligible, power_map = _build_inputs(toy_set_data)

    with pytest.raises(RuntimeError) as excinfo:
        solve_beam_search_bronze_with_emblems(
            champs=champs,
            champ_traits=champ_traits,
            trait_bps=trait_bps,
            eligible_traits=eligible,
            team_size=2,
            beam_width=10,
            hard_emblems={},
            max_emblems_total=0,
            power_map=power_map,
            required_champions=None,
            required_traits_min={"X": 3},
        )

    assert "constraints" in str(excinfo.value) or "Required trait" in str(excinfo.value)


def test_realistic_strict_requirements_have_unique_team():
    cfg = default_config()
    _, champs, champ_traits, trait_bps, _champ_cost, eligible_traits, _trait_freq = load_set_data(
        cfg.json_path, cfg.set_id
    )

    required_team = [
        "TFT16_Ashe",
        "TFT16_Kennen",
        "TFT16_Kobuko",
        "TFT16_Sejuani",
        "TFT16_Lissandra",
        "TFT16_Taric",
        "TFT16_Wukong",
        "TFT16_Yunara",
        "TFT16_Ryze",
    ]

    champs_pool = required_team
    champ_traits_pool = {c: champ_traits[c] for c in champs_pool}
    power_map = {c: 0.0 for c in champs_pool}

    req_champs = {"TFT16_Ryze": 1, "TFT16_Yunara": 1}
    req_traits = {"Yordle": 2, "Targon": 1, "Freljord": 3, "Ionia": 3}

    team, *_ = solve_beam_search_bronze_with_emblems(
        champs=champs_pool,
        champ_traits=champ_traits_pool,
        trait_bps=trait_bps,
        eligible_traits=eligible_traits,
        team_size=9,
        beam_width=50,
        hard_emblems={},
        max_emblems_total=0,
        power_map=power_map,
        required_champions=req_champs,
        required_traits_min=req_traits,
    )

    assert set(team) == set(required_team)
