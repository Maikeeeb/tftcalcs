from bfl.config_loader import load_config
from bfl.bronze_for_life import load_set_data


def test_blacklisted_trait_not_in_eligible(toy_set_data, tmp_path):
    # Write a temporary json file that looks like your en_us structure
    data = {"sets": {"16": toy_set_data}}
    p = tmp_path / "toy.json"
    p.write_text(__import__("json").dumps(data), encoding="utf-8")

    cfg = load_config(None)
    cfg.blacklist_traits_by_name = {"Targon"}

    set_data, champs, champ_traits, trait_bps, champ_cost, eligible, freq = load_set_data(
        str(p), "16", cfg.blacklist_traits_by_name
    )
    assert "Targon" not in eligible
