def solve_beam_search_bronze_with_emblems(champs: List[str],
                                          champ_traits: Dict[str, List[str]],
                                          trait_bps: Dict[str, List[int]],
                                          eligible_traits: Set[str],
                                          team_size: int,
                                          beam_width: int,
                                          hard_emblems: Dict[str, int],
                                          max_emblems_total: int,
                                          power_map: Dict[str, float]):
    """
    Beam search for max bronze-active traits, with emblems.
    Tie-breakers (in this order):
      1) bronze count (eligible, tier1-only)
      2) active eligible traits (any tier)
      3) fewer upgraded (tier2+)
      4) higher team power (from MetaTFT)
    """

    auto_candidates = sorted([t for t in eligible_traits if t not in hard_emblems])

    def choose_best_emblems(base_counts: Dict[str, int]) -> Dict[str, int]:
        if max_emblems_total <= 0:
            return dict(hard_emblems)

        chosen = dict(hard_emblems)

        def eval_with(chosen_emblems: Dict[str, int]) -> Tuple[int, int, int]:
            cnt2 = apply_emblem_starts(base_counts, chosen_emblems)
            bronze = 0
            active = 0
            upgraded = 0
            for t in eligible_traits:
                bps = trait_bps[t]
                c = cnt2.get(t, 0)
                if c < bps[0]:
                    continue
                active += 1
                if len(bps) == 1:
                    bronze += 1
                else:
                    if c < bps[1]:
                        bronze += 1
                    else:
                        upgraded += 1
            return bronze, active, upgraded

        already_used = sum(chosen.values())
        remaining = max(0, max_emblems_total - already_used)
        if remaining == 0:
            return chosen

        for _ in range(remaining):
            best_t = None
            best_key = None

            for t in auto_candidates:
                if t in chosen:
                    continue

                trial = dict(chosen)
                trial[t] = 1
                bronze, active, upgraded = eval_with(trial)
                key = (bronze, active, -upgraded)

                if best_key is None or key > best_key:
                    best_key = key
                    best_t = t

            if best_t is None:
                break
            chosen[best_t] = 1

        return chosen

    def score_state(base_counts: Dict[str, int]) -> Tuple[int, int, int, Dict[str, int]]:
        emblem_counts = choose_best_emblems(base_counts)
        cnt2 = apply_emblem_starts(base_counts, emblem_counts)

        bronze = 0
        active = 0
        upgraded = 0

        for t in eligible_traits:
            bps = trait_bps[t]
            c = cnt2.get(t, 0)
            if c < bps[0]:
                continue
            active += 1
            if len(bps) == 1:
                bronze += 1
            else:
                if c < bps[1]:
                    bronze += 1
                else:
                    upgraded += 1

        return bronze, active, upgraded, emblem_counts

    # Beam state: (team, base_counts, team_power, sort_key)
    beam: List[Tuple[List[str], Dict[str, int], float, Tuple[int, int, int, float]]] = [
        ([], defaultdict(int), 0.0, (0, 0, 0, 0.0))
    ]

    for _ in range(team_size):
        candidates = []
        for team, base_counts, team_power, _ in beam:
            team_set = set(team)
            for c in champs:
                if c in team_set:
                    continue

                new_team = team + [c]
                new_counts = defaultdict(int, base_counts)
                for t in champ_traits[c]:
                    new_counts[t] += 1

                bronze, active, upgraded, _ = score_state(new_counts)
                new_power = team_power + power_map.get(c, 0.0)

                key = (bronze, active, -upgraded, new_power)
                candidates.append((new_team, new_counts, new_power, key))

        candidates.sort(key=lambda x: x[3], reverse=True)
        beam = candidates[:beam_width]

        if not beam:
            break

    if not beam:
        raise RuntimeError("Beam search produced no candidates. Check filtering logic.")

    best_team, best_base_counts, best_power, best_key = max(beam, key=lambda x: x[3])

    emblem_counts = choose_best_emblems(best_base_counts)

    counts, bronze_traits, active_traits, upgraded_traits, used_traits = classify_traits(
        best_team, champ_traits, trait_bps, eligible_traits, emblem_counts
    )

    return best_team, emblem_counts, best_power, len(
        bronze_traits), counts, bronze_traits, active_traits, upgraded_traits, used_traits