# Freeze

(Research note for Football Passing Chain — what the freeze looked
like before the pass. Pre-freeze descriptors banked on 1,160 rows;
the loop-closure test nulled.)

The freeze gate 3 scores: press access, separation velocity, and
affordance volume at t=0. The shape pair is measured over the 5 s of
off-ball movement that produced the choice set; affordance is a state
over that set. Gate 0 describes freezes; it doesn't rate them —
no good/bad, no value function, no table link. Open-man counts cut:
repositioning without separation, noise with a name. Pipeline
position: freeze(0) → arrival(3) → control(4) → hold(1) → resolution(5).
Gate 0 abuts gate 3 (shape outputs are gate 3's inputs; affordance
reuses the gate-3 scorer frozen over the full set); it does not
feed gate 1 directly — hold timing is independent of press/separation
shape and of choice load (nulls in test_hold_freeze_null and test_load_hold).
## What it measures

- Press access at freeze: nearest-opponent distance to ball at t=0.
- Separation velocity: mean rate of change of open-man separation
  over [−5 s, 0], opponents frozen at t=0 — teammate motion relative
  to the final shape. Positive = men getting opener into the freeze.
  The one component gate 5 has no mirror for — formation is a
  derivative, resolution is a state.
- Affordance volume: viable-set size plus margin entropy over the
  frozen choice-set margins at t=0 (`affordance_volume` in
  `src/models/formation/mechanism.py`, threshold τ = 0.0 — viable-chosen
  takes rank 0 at the headline rate in every league,
  test_choice_viability). State over the outlet set, complementing the
  shape pair. Same gate-0 status: describes the freeze, rates nothing.
Per-freeze full sets banked separately by scripts/label_choice_sets.py
(`data/pooled/idsse_choice_sets_labeled.pkl`, n=1,160, frozen margins):
mean 9.9 outlets, 8.6 viable, effective 7.1; rank-0 share falls
0.53 → 0.08 across viable-size bins, monotone (test_choice_sets_table).

## Schematic grammar (L1, `scripts/freeze_schematic.py`, figs 13a–d)

One SVG per pinned freeze, banked fields only. Vertical outlet stack,
rank 0 top; bar length ∝ margin; rank label left; dashed τ line down
the stack (right of it = viable). Chosen outlet ringed green; best
unchosen hollow-marked (regret readable at a glance: ring below the top
slot). Header carries zone, control, hold + exit, n/n_v/effective,
pre-press/sep-vel, Δpress. Degenerate states drawn, never hidden:
singleton slot + "counted, never scored" tag; unscorable hatched stack
+ risk=None tag. No coordinates, no motion — time appears as text.
Four rows: median mid set (J03WN1), tail loosen Δpress +18.38 (J03WR9),
smallest set nv=3 (J03WMX), synthetic unscorable (grammar demo only).
Pinned in test_freeze_schematic; drift enforced by the figures gate.

## Loop test (nulled)

Regress pre-pass press access on previous-pass press-delta. Unfiltered
1,152 linked pairs: Pearson +0.10, Spearman +0.05 (R2~=1%). Detected at
n=1,152, not noise, and not usable. The pairing is diluted (median gap
8.6 s between linked rows, 39% within 5 s); gap<=5 s subset (n=452)
gives r=+0.25. Detected (R2~=6%, t=5.54), carried by turnover pairs
(previous uncontrolled: r=+0.42, n=227); the controlled intersection
(n=225, r=+0.13) is underpowered (MDE 0.19). The signal is phase-reset,
not a gate-5→gate-0 loop. Under the stated conditioning (previous reception
controlled, n=655) r=+0.02, null. Positive delta means loosened, so
6.34 m after loosening vs 5.73 m after tightening runs with persistence;
the loop hypothesis predicted tightening after loosening. The 0↔5
recurrence stays architecture, not evidence — gate 0 describes freezes
independently from here.

## Sources

IDSSE only for the fit. SkillCorner replicates shape direction,
never pools. 360 excluded (no time axis). Metrica mechanism tests only.
## Edge

Conditions on the previous pass's ΔS, which conditions on control, arrival, attempting: four selection gates upstream. Transition rates are E[Q | ΔS | controlled | arrived | attempted]. Deployment caveat carries forward: fit on pre-instrument formations drifts once teams optimize for openness — recalibrate on post-deployment sets.
