from bfl.solver import solve_beam_search_bronze_with_emblems


def test_traitless_unit_can_be_quality_anchor():
    champs = [
        "Traitless",
        "Tanky",
        "C1",
        "C2",
        "C3",
        "C4",
        "C5",
    ]

    champ_traits = {
        "Traitless": [],
        "Tanky": ["A"],
        "C1": ["B"],
        "C2": ["C"],
        "C3": ["D"],
        "C4": ["E"],
        "C5": ["F"],
    }

    trait_bps = {t: [1] for t in ["A", "B", "C", "D", "E", "F"]}
    eligible_traits = set(trait_bps)

    power_map = {
        "Traitless": 10.0,
        "Tanky": 9.0,
        "C1": 8.0,
        "C2": 7.0,
        "C3": 6.0,
        "C4": 5.0,
        "C5": 4.0,
    }

    team, emblems, *_ = solve_beam_search_bronze_with_emblems(
        champs=champs,
        champ_traits=champ_traits,
        trait_bps=trait_bps,
        eligible_traits=eligible_traits,
        team_size=7,
        beam_width=20,
        hard_emblems={},
        max_emblems_total=0,
        power_map=power_map,
        required_champions={"Traitless": 1},
        required_traits_min={},
        forced_units=None,
        trait_stats=None,
        tank_champions={"Tanky"},
        mode="bronze",
        champ_slot_sizes=None,
        trait_value_overrides=None,
        must_include_one_of=None,
        seed_verticals=False,
    )

    assert "Traitless" in team
    assert "Tanky" in team
    # All six eligible traits must be active to reach bronze>=6.
    assert set(emblems.keys()) == set()
    assert len(team) == 7
