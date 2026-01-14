from bfl.bronze_for_life import build_name_to_api_map, normalize_name


def test_build_name_to_api_map_handles_apiname_tail_and_punctuation():
    set_data = {
        "champions": [
            {"apiName": "TFT16_ChoGath", "name": "Cho'Gath", "characterName": "Cho'Gath"},
            {"apiName": "TFT16_THex", "name": "T-Hex", "characterName": "T-Hex"},
            {
                "apiName": "TFT16_LucianSenna",
                "name": "Lucian & Senna",
                "characterName": "Lucian & Senna",
            },
        ]
    }
    m = build_name_to_api_map(set_data)

    assert m[normalize_name("Cho'Gath")] == "TFT16_ChoGath"
    assert m[normalize_name("T-Hex")] == "TFT16_THex"
    assert m[normalize_name("Lucian & Senna")] == "TFT16_LucianSenna"
