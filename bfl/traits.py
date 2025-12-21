def apply_emblem_starts(counts: Dict[str, int], emblem_counts: Dict[str, int]) -> Dict[str, int]:
    out = defaultdict(int, counts)
    for t, v in emblem_counts.items():
        out[t] += v
    return dict(out)

def classify_traits(team: List[str],
                    champ_traits: Dict[str, List[str]],
                    trait_bps: Dict[str, List[int]],
                    eligible_traits: Set[str],
                    emblem_counts: Dict[str, int]):
    # base counts from team
    cnt = defaultdict(int)
    for c in team:
        for t in champ_traits[c]:
            cnt[t] += 1

    # add emblem starts
    cnt2 = apply_emblem_starts(cnt, emblem_counts)

    bronze = []
    active_any = []
    upgraded = []

    for t in eligible_traits:
        bps = trait_bps[t]
        c = cnt2.get(t, 0)
        if c < bps[0]:
            continue

        active_any.append(t)

        if len(bps) == 1:
            bronze.append(t)
        else:
            if c < bps[1]:
                bronze.append(t)
            else:
                upgraded.append(t)

    used = sorted({t for c in team for t in champ_traits[c]})
    return dict(cnt2), sorted(bronze), sorted(active_any), sorted(upgraded), used
