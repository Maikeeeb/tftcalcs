# Why a Ryze board may be impossible with heavy bans

The Bronze-for-Life solver only optimizes **eligible traits**. A trait is eligible
when it has breakpoints, appears on at least two champions, and is not
blacklisted in the config.

Key implications for the provided config:

- Ryze’s only listed trait in set 16 is `Rune Mage`, which appears on a single
  champion. Single-champion traits are excluded from the eligible set, so Ryze
  contributes nothing toward the objective the solver is trying to maximize.
- The config also blacklists `Targon`. Blacklisted traits are removed from the
  eligible pool even if they appear on multiple champions.

With Ryze forced onto every team and many other champions banned, the solver is
left with a smaller pool of units that can supply eligible traits. Because the
objective maximizes eligible bronze traits first, any lineup dominated by
ineligible traits (like Ryze’s) is pruned during the search, which is why no
board is found for the provided settings.

Recent changes allow traitless units to qualify as quality tanks/carries based
on power alone, but they still do not contribute bronze traits. If the remaining
playable pool cannot hit six bronze traits, the search will continue to fail.
