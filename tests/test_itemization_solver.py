from bfl.config import default_config
from bfl.itemization_solver import run_itemization_solver
from bfl.set_loader import load_set_data
from tests.fixtures_itemization import ITEMIZATION_FIXTURES


def test_itemization_prefers_completed_item_matches():
    config = default_config()
    config.mode = "itemization"
    config.available_completed_items = ["TFT_Item_InfinityEdge"]
    config.target_carries = ["TFT16_Jinx", "TFT16_Ahri"]

    result = run_itemization_solver(config)
    ranked = result["solution"]["ranked_candidates"]

    assert ranked[0]["champion"] == "TFT16_Jinx"
    assert ranked[0]["score"]["completed_items"] == 1


def test_itemization_needed_traits_break_ties():
    config = default_config()
    config.mode = "itemization"
    config.target_carries = ["TFT16_Jinx", "TFT16_Ahri"]

    _, _, champ_traits, trait_bps, _, _, _ = load_set_data(config.json_path, config.set_id)
    ahri_traits = champ_traits["TFT16_Ahri"]
    jinx_traits = set(champ_traits["TFT16_Jinx"])
    needed_trait = next(trait for trait in ahri_traits if trait in trait_bps and trait not in jinx_traits)
    config.needed_traits = [needed_trait]

    result = run_itemization_solver(config)
    ranked = result["solution"]["ranked_candidates"]

    assert ranked[0]["champion"] == "TFT16_Ahri"


def test_itemization_reforge_counts_as_full_item():
    config = default_config()
    config.mode = "itemization"
    config.allow_reforge = True
    config.available_completed_items = ["TFT_Item_GuardianAngel"]
    config.target_carries = ["TFT16_Jinx"]

    result = run_itemization_solver(config)
    ranked = result["solution"]["ranked_candidates"]

    assert ranked[0]["score"]["reforged_items"] == 1


def test_itemization_fixture_bf_gloves_prefers_jinx():
    fixture = ITEMIZATION_FIXTURES["bf_gloves"]
    config = default_config()
    config.mode = "itemization"
    config.available_components = fixture["available_components"]
    config.available_completed_items = fixture["available_completed_items"]
    config.target_carries = fixture["target_carries"]
    config.team_traits = fixture["team_traits"]
    config.needed_traits = fixture["needed_traits"]
    config.allow_reforge = fixture["allow_reforge"]

    result = run_itemization_solver(config)
    ranked = result["solution"]["ranked_candidates"]

    assert ranked[0]["champion"] == fixture["expected_top_carry"]


def test_itemization_normalizes_tutorial_component_items():
    config = default_config()
    config.mode = "itemization"
    config.available_components = [
        "TFTTutorial_Item_NeedlesslyLargeRod",
        "TFTTutorial_Item_NeedlesslyLargeRod",
    ]
    config.target_carries = ["TFT16_Ahri"]

    result = run_itemization_solver(config)
    ranked = result["solution"]["ranked_candidates"]

    assert ranked[0]["score"]["craftable_items"] == 1
    assert "TFT_Item_RabadonsDeathcap" in ranked[0]["score"]["craftable"]
