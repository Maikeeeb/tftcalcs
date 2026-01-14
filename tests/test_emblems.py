from bfl.bronze_for_life import apply_emblem_starts


def test_apply_emblem_starts_adds_to_existing_counts():
    base = {"X": 1, "Y": 2}
    emblems = {"X": 1, "Z": 1}
    out = apply_emblem_starts(base, emblems)

    assert out["X"] == 2
    assert out["Y"] == 2
    assert out["Z"] == 1
