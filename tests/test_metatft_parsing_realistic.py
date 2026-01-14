from bfl.bronze_for_life import parse_metatft_units
from bfl.metatft import metatft_to_unit_stats
from bfl.set_loader import load_set_data


def test_parse_metatft_units_ignores_items_and_still_parses_units():
    text = """
    Unit
    Tier
    Avg Place
    Win Rate
    Frequency
    Popular Items
    Unlockable UnitAlpha
    S
    3.50
    12.0%
    100,000 5.0%
    Infinity Edge
    Hand Of Justice
    Unlockable UnitBeta
    A
    4.10
    9.0%
    50,000 2.5%
    Guinsoo's Rageblade
    """
    raw = parse_metatft_units(text)

    assert "Alpha" in raw
    assert "Beta" in raw
    assert raw["Alpha"]["avg"] == 3.50
    assert abs(raw["Alpha"]["win"] - 0.12) < 1e-9
    assert abs(raw["Alpha"]["freq"] - 0.05) < 1e-9
    assert raw["Alpha"]["items"] == ["Infinity Edge", "Hand Of Justice"]
    assert raw["Beta"]["items"] == ["Guinsoo's Rageblade"]


def test_real_metatft_units_cover_solver_champions():
    set_data, champs, *_ = load_set_data("data/en_us.json", "16")

    with open("data/metatft_units.txt", "r", encoding="utf-8") as f:
        txt = f.read()

    stats = metatft_to_unit_stats(txt, set_data)

    missing = [c for c in champs if c not in stats]

    # Allow for a couple of missing entries in the paste, but not widespread gaps
    assert len(missing) <= 2, f"Missing MetaTFT stats for: {missing}"
