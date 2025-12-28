from bfl.bronze_for_life import parse_metatft_units

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
