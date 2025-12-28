from bfl.bronze_for_life import parse_metatft_units, metatft_to_unit_stats

def test_parse_metatft_units_basic():
    text = """
    Unit
    Tier
    Avg Place
    Win Rate
    Frequency
    Popular Items
    Alpha
    S
    3.50
    12.0%
    100,000 5.0%
    Infinity Edge
    """
    raw = parse_metatft_units(text)
    assert "Alpha" in raw
    assert raw["Alpha"]["avg"] == 3.50
    assert abs(raw["Alpha"]["win"] - 0.12) < 1e-9
    assert abs(raw["Alpha"]["freq"] - 0.05) < 1e-9
    assert raw["Alpha"]["items"] == ["Infinity Edge"]


def test_metatft_to_unit_stats_maps_to_api(toy_set_data):
    text = """
    Alpha
    S
    3.50
    12.0%
    100,000 5.0%
    """
    stats = metatft_to_unit_stats(text, toy_set_data)
    assert "TFT16_Alpha" in stats
    assert stats["TFT16_Alpha"]["avg"] == 3.50
