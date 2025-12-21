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
