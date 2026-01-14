#!/usr/bin/env python3
"""
TFT Set 16 Team Planner code helper (offline, no scraping).

- Encode:  python tft_teamplanner_code.py encode --names "Anivia" "Azir" "Bard"
- Decode:  python tft_teamplanner_code.py decode 0233e33533f018000000000000000000TFTSet16

This uses Riot client data (team_planner_code) from CommunityDragon:
  /latest/plugins/rcp-be-lol-game-data/global/default/v1/tftchampions-teamplanner.json
"""

from __future__ import annotations
import argparse, json, re, sys
from typing import List, Dict, Iterable

SET_SUFFIX = "TFTSet16"
PREFIX = "02"
SLOTS = 10  # observed planner code capacity (10 * 3 hex digits after the 02 prefix)

# Authoritative order (the client expects units in this order)
ORDER_IDS: List[str] = [
    "TFT16_Tristana",
    "TFT16_Lulu",
    "TFT16_Teemo",
    "TFT16_Rumble",
    "TFT16_Nautilus",
    "TFT16_TwistedFate",
    "TFT16_Gangplank",
    "TFT16_Illaoi",
    "TFT16_MissFortune",
    "TFT16_Sion",
    "TFT16_Briar",
    "TFT16_Draven",
    "TFT16_Ambessa",
    "TFT16_Zoe",
    "TFT16_Leona",
    "TFT16_Aphelios",
    "TFT16_Taric",
    "TFT16_JarvanIV",
    "TFT16_Sona",
    "TFT16_Garen",
    "TFT16_Lux",
    "TFT16_Anivia",
    "TFT16_Ashe",
    "TFT16_Braum",
    "TFT16_Lissandra",
    "TFT16_Milio",
    "TFT16_Neeko",
    "TFT16_Jinx",
    "TFT16_Caitlyn",
    "TFT16_Vi",
    "TFT16_Seraphine",
    "TFT16_Yasuo",
    "TFT16_Ahri",
    "TFT16_Wukong",
    "TFT16_Shen",
    "TFT16_Malzahar",
    "TFT16_RekSai",
    "TFT16_ChoGath",
    "TFT16_KogMaw",
    "TFT16_Annie",
    "TFT16_Ornn",
    "TFT16_Kindred",
    "TFT16_Azir",
    "TFT16_Zilean",
    "TFT16_Fiddlesticks",
    "TFT16_Shyvana",
    "TFT16_Galio",
    "TFT16_TahmKench",
    "TFT16_Sejuani",
    "TFT16_Sett",
    "TFT16_Brock",
    "TFT16_THex",
    "TFT16_BelVeth",
    "TFT16_Singed",
    "TFT16_AurelionSol",
    "TFT16_Veigar",
    "TFT16_BaronNashor",
    "TFT16_Darius",
    "TFT16_Yone",
    "TFT16_Warwick",
    "TFT16_Fizz",
    "TFT16_Poppy",
    "TFT16_Kennen",
    "TFT16_Ziggs",
    "TFT16_Aatrox",
    "TFT16_Volibear",
    "TFT16_Jhin",
    "TFT16_Sylas",
    "TFT16_Ryze",
    "TFT16_Nidalee",
    "TFT16_Tryndamere",
    "TFT16_RiftHerald",
    "TFT16_Mel",
    "TFT16_Graves",
    "TFT16_Skarner",
    "TFT16_Diana",
    "TFT16_Kaisa",
    "TFT16_Renekton",
    "TFT16_Nasus",
    "TFT16_Xerath",
    "TFT16_Thresh",
    "TFT16_Gwen",
    "TFT16_Kalista",
    "TFT16_Leblanc",
    "TFT16_Viego",
    "TFT16_Ekko",
    "TFT16_Bard",
    "TFT16_Vayne",
    "TFT16_Yunara",
    "TFT16_Swain",
    "TFT16_XinZhao",
    "TFT16_Yorick",
    "TFT16_Orianna",
    "TFT16_Qiyana",
    "TFT16_Loris",
    "TFT16_Blitzcrank",
    "TFT16_DrMundo",
    "TFT16_Zaahen",
    "TFT16_Lucian",
    "TFT16_Kobuko",
]

# Mappings
ID_TO_HEX: Dict[str, str] = {
    "TFT16_Tristana": "2DF",
    "TFT16_Lulu": "2E0",
    "TFT16_Teemo": "320",
    "TFT16_Rumble": "321",
    "TFT16_Nautilus": "322",
    "TFT16_TwistedFate": "323",
    "TFT16_Gangplank": "324",
    "TFT16_Illaoi": "32C",
    "TFT16_MissFortune": "32D",
    "TFT16_Sion": "32E",
    "TFT16_Briar": "32F",
    "TFT16_Draven": "331",
    "TFT16_Ambessa": "332",
    "TFT16_Zoe": "333",
    "TFT16_Leona": "334",
    "TFT16_Aphelios": "335",
    "TFT16_Taric": "336",
    "TFT16_JarvanIV": "338",
    "TFT16_Sona": "33A",
    "TFT16_Garen": "33C",
    "TFT16_Lux": "33D",
    "TFT16_Anivia": "33E",
    "TFT16_Ashe": "33F",
    "TFT16_Braum": "340",
    "TFT16_Lissandra": "341",
    "TFT16_Milio": "342",
    "TFT16_Neeko": "343",
    "TFT16_Jinx": "348",
    "TFT16_Caitlyn": "349",
    "TFT16_Vi": "34B",
    "TFT16_Seraphine": "34C",
    "TFT16_Yasuo": "34D",
    "TFT16_Ahri": "34F",
    "TFT16_Wukong": "350",
    "TFT16_Shen": "351",
    "TFT16_Malzahar": "352",
    "TFT16_RekSai": "353",
    "TFT16_ChoGath": "354",
    "TFT16_KogMaw": "355",
    "TFT16_Annie": "356",
    "TFT16_Ornn": "357",
    "TFT16_Kindred": "358",
    "TFT16_Azir": "359",
    "TFT16_Zilean": "35A",
    "TFT16_Fiddlesticks": "35B",
    "TFT16_Shyvana": "35D",
    "TFT16_Galio": "35F",
    "TFT16_TahmKench": "360",
    "TFT16_Sejuani": "361",
    "TFT16_Sett": "362",
    "TFT16_Brock": "363",
    "TFT16_THex": "365",
    "TFT16_BelVeth": "366",
    "TFT16_Singed": "367",
    "TFT16_AurelionSol": "368",
    "TFT16_Veigar": "369",
    "TFT16_BaronNashor": "36A",
    "TFT16_Darius": "36B",
    "TFT16_Yone": "36C",
    "TFT16_Warwick": "36D",
    "TFT16_Fizz": "36E",
    "TFT16_Poppy": "36F",
    "TFT16_Kennen": "370",
    "TFT16_Ziggs": "371",
    "TFT16_Aatrox": "372",
    "TFT16_Volibear": "373",
    "TFT16_Jhin": "374",
    "TFT16_Sylas": "012",
    "TFT16_Ryze": "013",
    "TFT16_Nidalee": "014",
    "TFT16_Tryndamere": "011",
    "TFT16_RiftHerald": "016",
    "TFT16_Mel": "019",
    "TFT16_Graves": "027",
    "TFT16_Skarner": "01A",
    "TFT16_Diana": "023",
    "TFT16_Kaisa": "01B",
    "TFT16_Renekton": "01C",
    "TFT16_Nasus": "022",
    "TFT16_Xerath": "01F",
    "TFT16_Thresh": "021",
    "TFT16_Gwen": "01D",
    "TFT16_Kalista": "01E",
    "TFT16_Leblanc": "017",
    "TFT16_Viego": "024",
    "TFT16_Ekko": "015",
    "TFT16_Bard": "018",
    "TFT16_Vayne": "004",
    "TFT16_Yunara": "02A",
    "TFT16_Swain": "025",
    "TFT16_XinZhao": "010",
    "TFT16_Yorick": "00F",
    "TFT16_Orianna": "02B",
    "TFT16_Qiyana": "02C",
    "TFT16_Loris": "020",
    "TFT16_Blitzcrank": "34A",
    "TFT16_DrMundo": "02F",
    "TFT16_Zaahen": "030",
    "TFT16_Lucian": "034",
    "TFT16_Kobuko": "035",
}
NAME_TO_ID: Dict[str, str] = {
    "tristana": "TFT16_Tristana",
    "lulu": "TFT16_Lulu",
    "teemo": "TFT16_Teemo",
    "rumble": "TFT16_Rumble",
    "nautilus": "TFT16_Nautilus",
    "twisted fate": "TFT16_TwistedFate",
    "gangplank": "TFT16_Gangplank",
    "illaoi": "TFT16_Illaoi",
    "miss fortune": "TFT16_MissFortune",
    "sion": "TFT16_Sion",
    "briar": "TFT16_Briar",
    "draven": "TFT16_Draven",
    "ambessa": "TFT16_Ambessa",
    "zoe": "TFT16_Zoe",
    "leona": "TFT16_Leona",
    "aphelios": "TFT16_Aphelios",
    "taric": "TFT16_Taric",
    "jarvan iv": "TFT16_JarvanIV",
    "sona": "TFT16_Sona",
    "garen": "TFT16_Garen",
    "lux": "TFT16_Lux",
    "anivia": "TFT16_Anivia",
    "ashe": "TFT16_Ashe",
    "braum": "TFT16_Braum",
    "lissandra": "TFT16_Lissandra",
    "milio": "TFT16_Milio",
    "neeko": "TFT16_Neeko",
    "jinx": "TFT16_Jinx",
    "caitlyn": "TFT16_Caitlyn",
    "vi": "TFT16_Vi",
    "seraphine": "TFT16_Seraphine",
    "yasuo": "TFT16_Yasuo",
    "ahri": "TFT16_Ahri",
    "wukong": "TFT16_Wukong",
    "shen": "TFT16_Shen",
    "malzahar": "TFT16_Malzahar",
    "rek'sai": "TFT16_RekSai",
    "cho'gath": "TFT16_ChoGath",
    "kog'maw": "TFT16_KogMaw",
    "annie": "TFT16_Annie",
    "ornn": "TFT16_Ornn",
    "kindred": "TFT16_Kindred",
    "azir": "TFT16_Azir",
    "zilean": "TFT16_Zilean",
    "fiddlesticks": "TFT16_Fiddlesticks",
    "shyvana": "TFT16_Shyvana",
    "galio": "TFT16_Galio",
    "tahm kench": "TFT16_TahmKench",
    "sejuani": "TFT16_Sejuani",
    "sett": "TFT16_Sett",
    "brock": "TFT16_Brock",
    "t-hex": "TFT16_THex",
    "bel'veth": "TFT16_BelVeth",
    "singed": "TFT16_Singed",
    "aurelion sol": "TFT16_AurelionSol",
    "veigar": "TFT16_Veigar",
    "baron nashor": "TFT16_BaronNashor",
    "darius": "TFT16_Darius",
    "yone": "TFT16_Yone",
    "warwick": "TFT16_Warwick",
    "fizz": "TFT16_Fizz",
    "poppy": "TFT16_Poppy",
    "kennen": "TFT16_Kennen",
    "ziggs": "TFT16_Ziggs",
    "aatrox": "TFT16_Aatrox",
    "volibear": "TFT16_Volibear",
    "jhin": "TFT16_Jhin",
    "sylas": "TFT16_Sylas",
    "ryze": "TFT16_Ryze",
    "nidalee": "TFT16_Nidalee",
    "tryndamere": "TFT16_Tryndamere",
    "rift herald": "TFT16_RiftHerald",
    "mel": "TFT16_Mel",
    "graves": "TFT16_Graves",
    "skarner": "TFT16_Skarner",
    "diana": "TFT16_Diana",
    "kai'sa": "TFT16_Kaisa",
    "renekton": "TFT16_Renekton",
    "nasus": "TFT16_Nasus",
    "xerath": "TFT16_Xerath",
    "thresh": "TFT16_Thresh",
    "gwen": "TFT16_Gwen",
    "kalista": "TFT16_Kalista",
    "leblanc": "TFT16_Leblanc",
    "viego": "TFT16_Viego",
    "ekko": "TFT16_Ekko",
    "bard": "TFT16_Bard",
    "vayne": "TFT16_Vayne",
    "yunara": "TFT16_Yunara",
    "swain": "TFT16_Swain",
    "xin zhao": "TFT16_XinZhao",
    "yorick": "TFT16_Yorick",
    "orianna": "TFT16_Orianna",
    "qiyana": "TFT16_Qiyana",
    "loris": "TFT16_Loris",
    "blitzcrank": "TFT16_Blitzcrank",
    "dr. mundo": "TFT16_DrMundo",
    "zaahen": "TFT16_Zaahen",
    "lucian & senna": "TFT16_Lucian",
    "kobuko & yuumi": "TFT16_Kobuko",
}

# Precompute sort key for ordering
ORDER_INDEX = {cid: i for i, cid in enumerate(ORDER_IDS)}


def _normalize_name(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def encode_team(ids: Iterable[str]) -> str:
    """Return a League-client compatible Team Planner code for Set 16."""
    ids = list(ids)

    # validate ids + dedupe preserving first occurrence
    seen = set()
    cleaned = []
    for cid in ids:
        if cid not in ID_TO_HEX:
            raise ValueError(f"Unknown character_id: {cid}")
        if cid in seen:
            continue
        seen.add(cid)
        cleaned.append(cid)

    # sort by official order
    cleaned.sort(key=lambda cid: ORDER_INDEX[cid])

    if len(cleaned) > SLOTS:
        raise ValueError(f"Too many units: {len(cleaned)} (max {SLOTS})")

    chunks = [ID_TO_HEX[cid].upper().zfill(3) for cid in cleaned]
    chunks += ["000"] * (SLOTS - len(chunks))
    return PREFIX + "".join(chunks) + SET_SUFFIX


def decode_team(code: str) -> List[str]:
    """Decode a Team Planner code into ordered character_ids (padding removed)."""
    code = code.strip()
    if not code.endswith(SET_SUFFIX):
        raise ValueError(f"Code must end with {SET_SUFFIX}")
    body = code[: -len(SET_SUFFIX)]
    if not body.startswith(PREFIX):
        raise ValueError("Code must start with '02'")

    hexpart = body[len(PREFIX) :]
    if len(hexpart) != SLOTS * 3:
        raise ValueError(f"Expected {SLOTS*3} hex chars after '02', got {len(hexpart)}")

    chunks = [hexpart[i : i + 3].upper() for i in range(0, len(hexpart), 3)]
    # drop trailing padding only
    while chunks and chunks[-1] == "000":
        chunks.pop()

    # reverse map
    hex_to_id = {v.upper(): k for k, v in ID_TO_HEX.items()}
    out = []
    for h in chunks:
        if h == "000":
            # In Set 16, '000' is padding (not a real unit in official team planner data).
            # Keep it if you want, but it won't paste into the League client as a unit.
            continue
        if h not in hex_to_id:
            out.append(f"UNKNOWN_{h}")
        else:
            out.append(hex_to_id[h])
    return out


def ids_from_names(names: Iterable[str]) -> List[str]:
    ids = []
    for n in names:
        key = _normalize_name(n)
        if key not in NAME_TO_ID:
            raise ValueError(f"Unknown unit name: {n}")
        ids.append(NAME_TO_ID[key])
    return ids


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    enc = sub.add_parser("encode")
    enc.add_argument("--ids", nargs="*", help="Use TFT16_* ids (character_id).", default=None)
    enc.add_argument("--names", nargs="*", help="Use display names like 'Anivia'.", default=None)

    dec = sub.add_parser("decode")
    dec.add_argument("code", help="Team planner code string")

    args = p.parse_args(argv)

    if args.cmd == "encode":
        if (args.ids is None and args.names is None) or (args.ids == [] and args.names == []):
            p.error("encode requires --ids or --names")
        if args.ids and args.names:
            p.error("use only one of --ids or --names")

        ids = args.ids if args.ids else ids_from_names(args.names)
        print(encode_team(ids))
        return 0

    if args.cmd == "decode":
        ids = decode_team(args.code)
        print("\n".join(ids))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
