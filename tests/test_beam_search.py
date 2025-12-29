from bfl.bronze_for_life import solve_beam_search_bronze_with_emblems


def test_beam_search_returns_valid_team(toy_set_data):
    champs = [c["apiName"] for c in toy_set_data["champions"]]
    champ_traits = {c["apiName"]: c["traits"] for c in toy_set_data["champions"]}
    trait_bps = {t["name"]: sorted(e["minUnits"] for e in t["effects"]) for t in toy_set_data["traits"]}
    eligible = {"X", "Y", "Z"}  # exclude W and Targon for bronze logic

    power_map = {c: 0.0 for c in champs}

    team, emblems, team_power, bronze_count, counts, bronze_traits, active_traits, upgraded_traits, used_traits = (
        solve_beam_search_bronze_with_emblems(
            champs=champs,
            champ_traits=champ_traits,
            trait_bps=trait_bps,
            eligible_traits=eligible,
            team_size=2,
            beam_width=50,
            hard_emblems={},
            max_emblems_total=0,
            power_map=power_map,
        )
    )

    assert len(team) == 2
    assert set(team).issubset(set(champs))
    assert isinstance(bronze_count, int)
    assert bronze_count >= 0


def test_beam_search_team_has_no_duplicates_and_correct_size(result_from_beam_search):
    team = result_from_beam_search  # adjust if your fixture returns tuple
    assert len(team) == len(set(team))


def test_beam_search_honors_special_slot_sizes_and_trait_values():
    champs = ["TFT16_BaronNashor", "TFT16_KogMaw", "TFT16_RekSai"]
    champ_traits = {c: ["Void"] for c in champs}
    trait_bps = {"Void": [2, 4]}
    eligible = {"Void"}
    power_map = {c: 0.0 for c in champs}

    slot_sizes = {"TFT16_BaronNashor": 2}
    trait_overrides = {"TFT16_BaronNashor": {"Void": 2}}

    team, _, _, _, counts, _, active_traits, _, _ = solve_beam_search_bronze_with_emblems(
        champs=champs,
        champ_traits=champ_traits,
        trait_bps=trait_bps,
        eligible_traits=eligible,
        team_size=3,
        beam_width=10,
        hard_emblems={},
        max_emblems_total=0,
        power_map=power_map,
        required_champions={"TFT16_BaronNashor": 1},
        champ_slot_sizes=slot_sizes,
        trait_value_overrides=trait_overrides,
    )

    assert len(team) == 2  # Baron counts as 2 slots, only one other unit fits
    assert counts["Void"] == 3
    assert active_traits == ["Void"]


def test_vertical_seeding_reaches_far_breakpoints():
    champs = ["StackA", "StackB", "StackC", "PowerD"]
    champ_traits = {
        "StackA": ["Stack"],
        "StackB": ["Stack"],
        "StackC": ["Stack"],
        "PowerD": ["Other"],
    }
    trait_bps = {"Stack": [3], "Other": [1]}
    eligible = {"Stack"}

    power_map = {"StackA": 0.0, "StackB": 0.0, "StackC": 0.0, "PowerD": 10.0}

    seeded_team, *_ = solve_beam_search_bronze_with_emblems(
        champs=champs,
        champ_traits=champ_traits,
        trait_bps=trait_bps,
        eligible_traits=eligible,
        team_size=3,
        beam_width=1,
        hard_emblems={},
        max_emblems_total=0,
        power_map=power_map,
        seed_verticals=True,
    )

    _, _, _, _, unseeded_counts, *_ = solve_beam_search_bronze_with_emblems(
        champs=champs,
        champ_traits=champ_traits,
        trait_bps=trait_bps,
        eligible_traits=eligible,
        team_size=3,
        beam_width=1,
        hard_emblems={},
        max_emblems_total=0,
        power_map=power_map,
        seed_verticals=False,
    )

    assert set(seeded_team) == {"StackA", "StackB", "StackC"}
    assert unseeded_counts.get("Stack", 0) < 3
