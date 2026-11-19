# Freeze

(Research note for Football Passing Chain — what the freeze looked
like before the pass. Pre-freeze descriptors banked on 1,160 rows;
the loop-closure test nulled.)

The freeze gate 3 scores: press access and separation velocity
at t=0, measured over the 5 s of off-ball movement that produced
the choice set. Gate 0 describes freezes; it doesn't rate them —
no good/bad, no value function, no table link. Open-man counts cut:
repositioning without separation, noise with a name. Pipeline
position: freeze(0) → arrival(3) → control(4) → hold(1) → resolution(5).
Gate 0 abuts gate 3 (its outputs are gate 3's inputs); it does not
feed gate 1 directly — hold timing is independent of pre-freeze
shape (pinned null in test_hold_freeze_null).
## What it measures

- Press access at freeze: nearest-opponent distance to ball at t=0.
- Separation velocity: mean rate of change of open-man separation
  over [−5 s, 0]. Positive = men getting opener into the freeze.
  The one component gate 5 has no mirror for — formation is a
  derivative, resolution is a state.

Banked on all 1,160 rows (1,159 with full −5 s tracks), same
label_retention.py run, backwards. Pinned in test_formation_table (means) and test_formation_transition (null loop).

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
