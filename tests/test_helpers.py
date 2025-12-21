from bfl.bronze_for_life import normalize_name, apply_emblem_starts, unit_power

def test_normalize_name():
    assert normalize_name("Lucian & Senna") == "luciansenna"
    assert normalize_name("Cho'Gath") == "chogath"
    assert normalize_name("T-Hex") == "thex"

def test_apply_emblem_starts():
    base = {"Zaun": 2, "Void": 1}
    emblems = {"Zaun": 1, "Ixtal": 1}
    out = apply_emblem_starts(base, emblems)
    assert out["Zaun"] == 3
    assert out["Void"] == 1
    assert out["Ixtal"] == 1

def test_unit_power_missing_stats_is_zero():
    assert unit_power("TFT16_A", {}) == 0.0

def test_unit_power_prefers_better_stats():
    stats = {
        "TFT16_A": {"win": 0.20, "avg": 4.0, "freq": 0.10},
        "TFT16_B": {"win": 0.10, "avg": 5.0, "freq": 0.10},
    }
    assert unit_power("TFT16_A", stats) > unit_power("TFT16_B", stats)
