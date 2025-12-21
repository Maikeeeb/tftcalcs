from bronze_for_life import load_set_data


def test_blacklisted_trait_not_in_eligible(toy_set_data, monkeypatch, tmp_path):
    # Write a temporary json file that looks like your en_us structure
    data = {"sets": {"16": toy_set_data}}
    p = tmp_path / "toy.json"
    p.write_text(__import__("json").dumps(data), encoding="utf-8")

    # Monkeypatch blacklist to include Targon (like real code)
    # If your blacklist is module-level constant, import module and patch it.
    import bronze_for_life as bfl
    bfl.BLACKLIST_TRAITS_BY_NAME = {"Targon"}

    set_data, champs, champ_traits, trait_bps, champ_cost, eligible, freq = load_set_data(str(p), "16")
    assert "Targon" not in eligible
