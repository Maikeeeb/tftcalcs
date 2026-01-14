from bfl.metatft import NEUTRAL_AVG_PLACEMENT, pessimistic_avg, trait_power, unit_power, TraitStat


def test_pessimistic_avg_respects_frequency_confidence():
    low_freq = pessimistic_avg(4.5, 0.05)
    high_freq = pessimistic_avg(4.5, 0.6)

    assert low_freq > high_freq
    assert low_freq > 4.5
    assert high_freq < low_freq


def test_unit_power_penalizes_high_average_and_rewards_frequency():
    stats = {
        "UnitA": {"win": 0.07, "avg": 4.5, "freq": 0.02},
        "UnitB": {"win": 0.07, "avg": 5.2, "freq": 0.02},
        "UnitC": {"win": 0.07, "avg": 4.5, "freq": 0.8},
    }

    # Lower average placement should beat higher average placement with other stats equal
    assert unit_power("UnitA", stats) > unit_power("UnitB", stats)
    # Higher frequency should narrow pessimism and improve power
    assert unit_power("UnitC", stats) > unit_power("UnitA", stats)


def test_trait_power_uses_pessimistic_average():
    trait_stats = {
        "Noxus": [TraitStat(required=3, tier="D", avg=5.04, win=0.07, freq=0.01)],
        "Void": [TraitStat(required=3, tier="S", avg=3.8, win=0.18, freq=0.2)],
    }

    noxus_score = trait_power("Noxus", 5, trait_stats)
    void_score = trait_power("Void", 3, trait_stats)

    assert noxus_score < 0  # poor average with low frequency is penalized
    assert void_score > 0  # strong average with decent frequency is rewarded
    # If a trait barely beats the neutral baseline, frequency pessimism keeps it near zero
    near_neutral = trait_power(
        "Noxus",
        3,
        {
            "Noxus": [
                TraitStat(required=3, tier="C", avg=NEUTRAL_AVG_PLACEMENT, win=0.07, freq=0.05)
            ]
        },
    )
    assert near_neutral < 0.2
