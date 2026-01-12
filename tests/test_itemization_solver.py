from bfl.config import default_config
from bfl.itemization_solver import run_itemization_solver
from bfl.set_loader import load_set_data


def test_itemization_prefers_completed_item_matches():
    config = default_config()
    config.mode = "itemization"
    config.itemization_completed_items = ["TFT_Item_InfinityEdge"]
    config.itemization_candidate_champions = ["TFT16_Jinx", "TFT16_Ahri"]

    result = run_itemization_solver(config)
    ranked = result["solution"]["ranked_candidates"]

    assert ranked[0]["champion"] == "TFT16_Jinx"
    assert ranked[0]["score"]["completed_items"] == 1


def test_itemization_needed_traits_break_ties():
    config = default_config()
    config.mode = "itemization"
    config.itemization_candidate_champions = ["TFT16_Jinx", "TFT16_Ahri"]

    _, _, champ_traits, trait_bps, _, _, _ = load_set_data(config.json_path, config.set_id)
    ahri_traits = champ_traits["TFT16_Ahri"]
    jinx_traits = set(champ_traits["TFT16_Jinx"])
    needed_trait = next(trait for trait in ahri_traits if trait in trait_bps and trait not in jinx_traits)
    config.itemization_needed_traits = [needed_trait]

    result = run_itemization_solver(config)
    ranked = result["solution"]["ranked_candidates"]

    assert ranked[0]["champion"] == "TFT16_Ahri"
