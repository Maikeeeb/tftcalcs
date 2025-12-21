# Traits that should NEVER count for Bronze for Life even if active.
BLACKLIST_TRAITS_BY_NAME: Set[str] = {
    "Targon",
}

# --- Emblem modeling (simple) ---
# If a trait is in EMBLEM_START_COUNTS, it starts at that many units (e.g., 1 emblem => +1).
EMBLEM_START_COUNTS: Dict[str, int] = {
    "Zaun": 1,
    "Ixtal": 1,
    "Freljord": 1,
    "Bilgewater": 1,
}

# If > 0, the optimizer will choose up to this many traits to receive +1 starting count (emblem),
# unless you hard-code EMBLEM_START_COUNTS above (hard-coded counts are always applied).
MAX_EMBLEMS_TOTAL = 0  # set 0 to disable automatic emblem selection