from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Tuple

from bfl.config import Config
from bfl.config_loader import validate_config_against_data
from bfl.io_utils import retry_file_operation
from bfl.set_loader import load_set_data


class ItemizationError(RuntimeError):
    """Raised when itemization execution fails but a debug log is available."""

    def __init__(self, message: str, debug_log: List[str], context: Dict[str, object]):
        super().__init__(message)
        self.debug_log = debug_log
        self.context = context


CARRY_ITEM_PREFERENCES: Dict[str, List[str]] = {
    "TFT16_Jinx": [
        "TFT_Item_InfinityEdge",
        "TFT_Item_LastWhisper",
        "TFT_Item_MadredsBloodrazor",
    ],
    "TFT16_Caitlyn": [
        "TFT_Item_Deathblade",
        "TFT_Item_LastWhisper",
        "TFT_Item_MadredsBloodrazor",
    ],
    "TFT16_Kaisa": [
        "TFT_Item_GuinsoosRageblade",
        "TFT_Item_LastWhisper",
        "TFT_Item_MadredsBloodrazor",
    ],
    "TFT16_Aphelios": [
        "TFT_Item_GuinsoosRageblade",
        "TFT_Item_Deathblade",
        "TFT_Item_LastWhisper",
    ],
    "TFT16_Ahri": [
        "TFT_Item_JeweledGauntlet",
        "TFT_Item_RabadonsDeathcap",
        "TFT_Item_BlueBuff",
    ],
}


@dataclass(frozen=True)
class ItemCatalog:
    """Catalog of TFT items with lookup capabilities.

    Provides mappings for resolving item names to apiNames and accessing
    item data including components, craftable items, and compositions.

    Attributes
    ----------
    items_by_api : Dict[str, Mapping[str, object]]
        Mapping from item apiName to full item data.
    components_by_key : Dict[str, Mapping[str, object]]
        Mapping from normalized component name to component item data.
    craftable_by_key : Dict[str, Mapping[str, object]]
        Mapping from normalized craftable item name to item data.
    component_api_names : set[str]
        Set of all component item apiNames.
    craftable_api_names : set[str]
        Set of all craftable item apiNames.
    compositions : Dict[str, Tuple[str, str]]
        Mapping from craftable item apiName to tuple of component apiNames.
    component_aliases : Dict[str, str]
        Mapping from tutorial component apiNames to standard apiNames.
    craftable_aliases : Dict[str, str]
        Mapping from tutorial craftable apiNames to standard apiNames.
    """

    items_by_api: Dict[str, Mapping[str, object]]
    components_by_key: Dict[str, Mapping[str, object]]
    craftable_by_key: Dict[str, Mapping[str, object]]
    component_api_names: set[str]
    craftable_api_names: set[str]
    compositions: Dict[str, Tuple[str, str]]
    component_aliases: Dict[str, str]
    craftable_aliases: Dict[str, str]


def _normalize_key(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def load_item_catalog(path: Path | str) -> ItemCatalog:
    """Load item catalog from Riot's set data JSON file.

    Parses the items section of the set data file and builds lookup structures
    for components, craftable items, and their relationships. Handles tutorial
    item aliases by mapping them to standard item apiNames.

    Parameters
    ----------
    path : Path | str
        Path to the Riot set data JSON file (e.g., en_us.json).

    Returns
    -------
    ItemCatalog
        Catalog object with all item lookup structures populated.
    """

    @retry_file_operation()
    def _load_file():
        with Path(path).open("r", encoding="utf-8") as f:
            return json.load(f)

    data = _load_file()

    raw_items = data.get("items", [])
    items = sorted(raw_items, key=lambda item: item.get("apiName", ""))
    items_by_api = {item.get("apiName"): item for item in items if item.get("apiName")}

    component_api_names = {
        item["apiName"]
        for item in items
        if item.get("apiName") and "component" in set(item.get("tags") or [])
    }

    craftable_api_names = {
        item["apiName"]
        for item in items
        if item.get("apiName")
        and isinstance(item.get("composition"), list)
        and len(item.get("composition")) == 2
        and set(item.get("composition", [])) <= component_api_names
    }

    components_by_key: Dict[str, Mapping[str, object]] = {}
    craftable_by_key: Dict[str, Mapping[str, object]] = {}
    compositions: Dict[str, Tuple[str, str]] = {}

    def _prefer_standard_item(
        existing: Mapping[str, object] | None, candidate: Mapping[str, object]
    ) -> bool:
        if existing is None:
            return True
        existing_api = str(existing.get("apiName", ""))
        candidate_api = str(candidate.get("apiName", ""))
        if existing_api.startswith("TFTTutorial_") and not candidate_api.startswith("TFTTutorial_"):
            return True
        return False

    for item in items:
        api = item.get("apiName")
        name = item.get("name")
        if not api or not name:
            continue
        normalized_name = _normalize_key(name)
        if api in component_api_names:
            if _prefer_standard_item(components_by_key.get(normalized_name), item):
                components_by_key[normalized_name] = item
        if api in craftable_api_names:
            if _prefer_standard_item(craftable_by_key.get(normalized_name), item):
                craftable_by_key[normalized_name] = item
            comps = item.get("composition") or []
            if len(comps) == 2:
                compositions[api] = (comps[0], comps[1])

    component_aliases: Dict[str, str] = {}
    craftable_aliases: Dict[str, str] = {}
    for item in items:
        api = item.get("apiName")
        name = item.get("name")
        if not api or not name:
            continue
        normalized_name = _normalize_key(name)
        if api.startswith("TFTTutorial_") and api in component_api_names:
            preferred = components_by_key.get(normalized_name)
            if preferred and preferred.get("apiName") != api:
                component_aliases[api] = str(preferred.get("apiName"))
        if api.startswith("TFTTutorial_") and api in craftable_api_names:
            preferred = craftable_by_key.get(normalized_name)
            if preferred and preferred.get("apiName") != api:
                craftable_aliases[api] = str(preferred.get("apiName"))

    return ItemCatalog(
        items_by_api=items_by_api,
        components_by_key=components_by_key,
        craftable_by_key=craftable_by_key,
        component_api_names=component_api_names,
        craftable_api_names=craftable_api_names,
        compositions=compositions,
        component_aliases=component_aliases,
        craftable_aliases=craftable_aliases,
    )


def _resolve_item(raw_value: str, catalog: ItemCatalog, *, kind: str) -> str:
    if raw_value in catalog.items_by_api:
        api_name = raw_value
    else:
        key = _normalize_key(raw_value)
        if kind == "component":
            item = catalog.components_by_key.get(key)
        elif kind == "completed":
            item = catalog.craftable_by_key.get(key)
        else:
            raise ItemizationError(f"Unknown item kind '{kind}'.")
        if not item:
            raise ItemizationError(f"Unknown {kind} item: {raw_value}")
        api_name = item["apiName"]

    if kind == "component" and api_name not in catalog.component_api_names:
        raise ItemizationError(f"Item '{raw_value}' is not a component.")
    if kind == "completed" and api_name not in catalog.craftable_api_names:
        raise ItemizationError(f"Item '{raw_value}' is not a craftable completed item.")

    if kind == "component" and api_name in catalog.component_aliases:
        api_name = catalog.component_aliases[api_name]
    if kind == "completed" and api_name in catalog.craftable_aliases:
        api_name = catalog.craftable_aliases[api_name]

    return api_name


def _resolve_items(values: Iterable[str], catalog: ItemCatalog, *, kind: str) -> List[str]:
    resolved = []
    for value in values:
        resolved.append(_resolve_item(str(value), catalog, kind=kind))
    return resolved


def _validate_preferences(preferences: Mapping[str, List[str]], catalog: ItemCatalog) -> None:
    invalid: Dict[str, List[str]] = {}
    for champ, items in preferences.items():
        missing = [item for item in items if item not in catalog.craftable_api_names]
        if missing:
            invalid[champ] = missing
    if invalid:
        raise ItemizationError(f"Preferred items not craftable: {invalid}")


def _score_items(
    preferred_items: List[str],
    completed_counts: Counter[str],
    component_counts: Counter[str],
    compositions: Mapping[str, Tuple[str, str]],
    *,
    allow_reforge: bool,
) -> Dict[str, object]:
    matched_completed: List[str] = []
    completed_used: Counter[str] = Counter()
    remaining: List[str] = []
    for item in sorted(preferred_items):
        if completed_counts[item] > completed_used[item]:
            completed_used[item] += 1
            matched_completed.append(item)
        else:
            remaining.append(item)

    reforged_items: List[str] = []
    if allow_reforge:
        available_reforges = sum(completed_counts.values()) - sum(completed_used.values())
        if available_reforges > 0:
            for item in list(remaining):
                if available_reforges <= 0:
                    break
                reforged_items.append(item)
                remaining.remove(item)
                available_reforges -= 1

    craftable_items: List[str] = []
    partial_items: List[Dict[str, object]] = []
    partial_components = 0
    remaining_components = component_counts.copy()

    for item in sorted(remaining):
        components = compositions.get(item)
        if not components:
            partial_items.append({"item": item, "components_hit": 0, "missing_components": []})
            continue
        if all(remaining_components[comp] > 0 for comp in components):
            for comp in components:
                remaining_components[comp] -= 1
            craftable_items.append(item)
        else:
            components_hit = sum(1 for comp in components if remaining_components[comp] > 0)
            partial_components += components_hit
            partial_items.append(
                {
                    "item": item,
                    "components_hit": components_hit,
                    "missing_components": [
                        comp for comp in components if remaining_components[comp] == 0
                    ],
                }
            )

    full_items = len(matched_completed) + len(reforged_items) + len(craftable_items)
    return {
        "full_items": full_items,
        "completed_items": len(matched_completed),
        "reforged_items": len(reforged_items),
        "craftable_items": len(craftable_items),
        "partial_components": partial_components,
        "matched_completed": matched_completed,
        "reforged": reforged_items,
        "craftable": craftable_items,
        "partial": partial_items,
    }


def run_itemization_solver(config: Config) -> Dict[str, object]:
    """Score carry candidates by item completion proximity and trait fit."""

    decision_log: List[str] = []
    decision_log.append(f"config: {json.dumps(config.to_dict(), sort_keys=True)}")

    context_details: Dict[str, object] = {"config": config.to_dict()}

    try:
        _, champs, champ_traits, trait_bps, champ_cost, _, _ = load_set_data(
            config.json_path, config.set_id, config.blacklist_traits_by_name
        )
        validate_config_against_data(config, champs, trait_bps)

        catalog = load_item_catalog(config.json_path)
        _validate_preferences(CARRY_ITEM_PREFERENCES, catalog)

        available_components = _resolve_items(
            config.available_components, catalog, kind="component"
        )
        available_completed = _resolve_items(
            config.available_completed_items, catalog, kind="completed"
        )

        team_traits = {str(t) for t in config.team_traits}
        needed_traits = {str(t) for t in config.needed_traits}

        if config.target_carries:
            candidate_champs = [champ for champ in config.target_carries if champ in champs]
        else:
            candidate_champs = [champ for champ in CARRY_ITEM_PREFERENCES if champ in champs]

        candidate_champs = sorted(set(candidate_champs))
        completed_counts = Counter(available_completed)
        component_counts = Counter(available_components)

        ranked: List[Dict[str, object]] = []
        for champ in candidate_champs:
            preferred_items = CARRY_ITEM_PREFERENCES.get(champ, [])
            item_score = _score_items(
                preferred_items,
                completed_counts,
                component_counts,
                catalog.compositions,
                allow_reforge=config.allow_reforge,
            )
            traits = champ_traits.get(champ, [])
            trait_set = set(traits)
            needed_matches = sorted(trait_set & needed_traits)
            team_matches = sorted(trait_set & team_traits)
            needed_hits = len(needed_matches)
            team_hits = len(team_matches)
            missing_components = sorted(
                {comp for item in item_score["partial"] for comp in item["missing_components"]}
            )
            ranked.append(
                {
                    "champion": champ,
                    "cost": champ_cost.get(champ),
                    "traits": traits,
                    "ideal_items": preferred_items,
                    "missing_components": missing_components,
                    "trait_shells": sorted(trait_set),
                    "team_trait_matches": team_matches,
                    "needed_trait_matches": needed_matches,
                    "suggested_slams": sorted(
                        set(item_score["craftable"]) | set(item_score["reforged"])
                    ),
                    "score": {
                        **item_score,
                        "needed_trait_hits": needed_hits,
                        "team_trait_hits": team_hits,
                    },
                }
            )
    except Exception as exc:
        decision_log.append(f"error: {exc}")
        raise ItemizationError(str(exc), decision_log, context_details) from exc

    ranked.sort(
        key=lambda entry: (
            -entry["score"]["full_items"],
            -entry["score"]["completed_items"],
            -entry["score"]["reforged_items"],
            -entry["score"]["craftable_items"],
            -entry["score"]["partial_components"],
            -entry["score"]["needed_trait_hits"],
            -entry["score"]["team_trait_hits"],
            entry["champion"],
        )
    )

    item_names = {api: item.get("name", api) for api, item in catalog.items_by_api.items() if api}

    return {
        "context": {
            "mode": config.mode,
            "set_id": config.set_id,
            "json_path": str(config.json_path),
            "candidate_count": len(candidate_champs),
            "team_traits": sorted(team_traits),
            "needed_traits": sorted(needed_traits),
            "available_components": available_components,
            "available_completed_items": available_completed,
            "allow_reforge": config.allow_reforge,
        },
        "solution": {
            "ranked_candidates": ranked,
        },
        "items": {
            "components": sorted(set(available_components)),
            "completed_items": sorted(set(available_completed)),
            "names_by_api": item_names,
        },
        "debug_log": decision_log,
    }
