from bfl.bronze_for_life import classify_traits


def test_classify_traits_bronze_vs_upgraded(toy_set_data):
    champ_traits = {c["apiName"]: c["traits"] for c in toy_set_data["champions"]}
    trait_bps = {
        t["name"]: sorted(e["minUnits"] for e in t["effects"]) for t in toy_set_data["traits"]
    }

    eligible = {"X", "Y", "Z"}  # W is exclusive, Targon blacklisted in real code

    team = ["TFT16_Alpha", "TFT16_Beta"]  # X=2 -> active, bronze (tier2 at 4)
    counts, bronze, active_any, upgraded, used = classify_traits(
        team, champ_traits, trait_bps, eligible, emblem_counts={}
    )

    assert counts["X"] == 2
    assert "X" in bronze
    assert "X" in active_any
    assert "X" not in upgraded


def test_classify_traits_with_emblem_start(toy_set_data):
    champ_traits = {c["apiName"]: c["traits"] for c in toy_set_data["champions"]}
    trait_bps = {
        t["name"]: sorted(e["minUnits"] for e in t["effects"]) for t in toy_set_data["traits"]
    }

    eligible = {"X", "Y", "Z"}

    team = ["TFT16_Alpha"]  # X=1, plus emblem X=+1 => 2 activates
    counts, bronze, active_any, upgraded, used = classify_traits(
        team, champ_traits, trait_bps, eligible, emblem_counts={"X": 1}
    )

    assert counts["X"] == 2
    assert "X" in bronze
    assert "X" in active_any


def test_classify_traits_supports_trait_value_overrides():
    champ_traits = {
        "TFT16_BaronNashor": ["Void"],
        "TFT16_KogMaw": ["Void"],
    }
    trait_bps = {"Void": [2, 4]}

    eligible = {"Void"}
    overrides = {"TFT16_BaronNashor": {"Void": 2}}

    team = ["TFT16_BaronNashor", "TFT16_KogMaw"]
    counts, bronze, active_any, upgraded, used = classify_traits(
        team,
        champ_traits,
        trait_bps,
        eligible,
        emblem_counts={},
        trait_value_overrides=overrides,
    )

    assert counts["Void"] == 3
    assert bronze == ["Void"]
    assert active_any == ["Void"]
