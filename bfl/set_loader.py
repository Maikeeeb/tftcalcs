def load_set_data(path: str, set_id: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    set_data = data["sets"][set_id]

    # Trait NAME -> sorted list of breakpoints (minUnits)
    trait_bps: Dict[str, List[int]] = {}
    for tr in set_data["traits"]:
        name = tr["name"]
        bps = sorted(
            e["minUnits"]
            for e in tr.get("effects", [])
            if e.get("minUnits") is not None
        )
        if bps:
            trait_bps[name] = bps

    # Known non-units inside champions
    EXCLUDE_API = {
        "TFT5_EmblemArmoryKey",
        "TFT_ArmoryKeyCompleted",
        "TFT_ArmoryKeyComponent",
        "TFT_ArmoryKeyOrnn",
        "TFT_ArmoryKeySupport",
        "TFT6_MercenaryChest",
    }

    champs: List[str] = []
    champ_traits: Dict[str, List[str]] = {}
    champ_cost: Dict[str, int] = {}

    for ch in set_data["champions"]:
        c_api = ch.get("apiName", "")

        # Remove fake entries
        if c_api in EXCLUDE_API:
            continue
        if ("ArmoryKey" in c_api) or ("MercenaryChest" in c_api):
            continue

        cost = ch.get("cost", None)
        if not isinstance(cost, int):
            continue

        # Optional heuristic: real units are normally 1-5 cost
        # If you later notice legit units outside 1-5, comment these out.
        if cost < 1 or cost > 5:
            continue

        traits = [t for t in ch.get("traits", []) if t in trait_bps]
        if not traits:
            continue

        champs.append(c_api)
        champ_traits[c_api] = traits
        champ_cost[c_api] = cost

    # Detect "exclusive traits" (appear on only 1 champion)
    trait_freq = defaultdict(int)
    for c in champs:
        for t in set(champ_traits[c]):
            trait_freq[t] += 1

    # Eligible for Bronze for Life:
    # - appears on 2+ champs
    # - has breakpoints
    # - not blacklisted
    eligible_traits: Set[str] = {
        t for t, f in trait_freq.items()
        if f >= 2 and t in trait_bps and t not in BLACKLIST_TRAITS_BY_NAME
    }

    return set_data, champs, champ_traits, trait_bps, champ_cost, eligible_traits, dict(trait_freq)