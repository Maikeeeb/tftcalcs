# Why a Ryze board may be impossible with heavy bans

Ryze mode now optimizes for **region traits only**. Eligible regions are:
Bilgewater, Demacia, Freljord, Ionia, Ixtal, Noxus, Piltover, Shadow Isles,
Shurima, Targon, Void, Yordle, and Zaun. When you pick this mode, the solver
also assumes a 9-unit board and requires `TFT16_Ryze` by default.

Even with the new focus, the solver can still fail to find a board if bans or
filters remove too many region-bearing champions:

- If you ban most units from a region, the search may not reach six active
  regions—the hard floor for Bronze-for-Life style scoring.
- If region traits are present but all surviving carriers are low power, they
  might not satisfy the quality constraints for a tank and a carry.

The Bronze-for-Life and Standard modes are unaffected by these rules; they keep
using the original eligible-trait logic. If you want Ryze to be optional in
Ryze mode (e.g., for World Runes augment quests requiring 4 active regions),
explicitly set `"required_champions": {"TFT16_Ryze": 0}` (optional) or
`"required_champions": {"TFT16_Ryze": -1}` (banned). The solver will still
default to `team_size=9` unless you explicitly override it.
