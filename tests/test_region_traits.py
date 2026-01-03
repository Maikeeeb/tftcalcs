from bfl.solver_api import region_trait_pool


def test_region_trait_pool_filters_to_regions():
    trait_bps = {
        "Bilgewater": [1],
        "Zaun": [2],
        "NonRegion": [1],
    }

    assert region_trait_pool(trait_bps) == {"Bilgewater", "Zaun"}
