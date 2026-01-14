from bfl.bronze_for_life import classify_traits


def test_classify_traits_uses_fixture_names_not_hardcoded(toy_set_data):
    champ_traits = {c["apiName"]: c["traits"] for c in toy_set_data["champions"]}
    trait_bps = {
        t["name"]: sorted(e["minUnits"] for e in t["effects"]) for t in toy_set_data["traits"]
    }
    eligible = {"X", "Y", "Z"}

    alpha = next(c["apiName"] for c in toy_set_data["champions"] if c["name"] == "Alpha")
    beta = next(c["apiName"] for c in toy_set_data["champions"] if c["name"] == "Beta")

    counts, bronze, active_any, upgraded, used = classify_traits(
        [alpha, beta], champ_traits, trait_bps, eligible, emblem_counts={}
    )

    assert counts["X"] == 2
    assert "X" in bronze
