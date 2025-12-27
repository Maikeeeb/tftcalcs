from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from bfl.config import default_config
from bfl.set_loader import load_set_data


@lru_cache(maxsize=None)
def _load_champions(json_path: str, set_id: str) -> tuple[str, ...]:
    """Load and cache playable champion apiNames for a given set.

    Parameters
    ----------
    json_path: str
        Path to the Riot set data (e.g., ``en_us.json``).
    set_id: str
        Identifier for the desired set inside the JSON payload.

    Returns
    -------
    tuple[str, ...]
        Playable champion apiNames matching the solver's filtering rules.
    """

    _, champs, *_ = load_set_data(json_path, set_id)
    return tuple(champs)


def list_playable_champions(
    json_path: str | Path | None = None, set_id: str | None = None
) -> List[str]:
    """Enumerate playable champions for the requested set.

    Defaults fall back to the repo's bundled set data and set id when parameters
    are omitted. Results are cached per (json_path, set_id) pair to avoid
    repeated parsing when called from UIs or validation hooks.
    """

    cfg = default_config()
    resolved_path = Path(json_path or cfg.json_path).expanduser()
    resolved_set = str(set_id or cfg.set_id)

    return list(_load_champions(str(resolved_path), resolved_set))
