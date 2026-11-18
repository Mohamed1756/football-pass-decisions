# Attempt

(Research note for Football Passing Chain — how long the ball sticks
before the next action. First fit banked on 1,160 intervals.)

The unplayed ball is unobserved: no event+tracking dataset records
the pass not played. So gate 1 does not model the decision — it
models its duration. Given control at receipt, how long until the
next pass attempt, loss, or stoppage?

`E[T_hold | control, zone]` — expected hold time given a controlled
reception, by reception zone. The clock starts where control does
(same t=0 as gate 5); the freeze is context, not condition.
Pipeline position: freeze(0) → arrival(3) → control(4) → hold(1) →
resolution(5). Hold timing is independent of pre-freeze shape
(pinned null in test_hold_freeze_null) — gate 1 conditions on
control, not on formation.
Headline object is the distribution: report median hold (holds skew
right; mean follows outliers) with the 3 s pass rate as diagnostic.
The 3 s is reused from gate 5's pinned timescale (median next-pass
2.4 s) to keep the gates comparable — an independent hold-duration
derivation would be cleaner, sensitivity at ±1 s untested either way.

## Why not whether

- The full whether (pass vs hold indefinitely at arbitrary moments)
  needs the unplayed ball: a label that doesn't exist in any banked
  pool or public dataset surveyed (timing/availability/EPO families
  reviewed; none isolates the attempt decision — Decroos comes nearest
  with action rates but bundles when inside a joint GRNN that can't
  run on our pools).
- Hold duration is observable today: every reception starts a
  possession interval ending in pass/loss/stoppage on IDSSE events +
  tracking. Same conditioning as every other gate (controlled |
  arrived | attempted); the true whether for non-receipt moments
  stays unbuilt and named.

## Calibration (1,160 intervals, by zone x exit)

- Median hold 2.16 s overall (q25 1.36, q75 3.92, mean 6.74 pulled
  by long tails): mid releases fastest (1.96), edges hold longer
  (def 2.52, att 2.34). Pass exits dominate everywhere (958/1160);
  loss is the minority exit in all three zones (57/89/56).
  Pinned in test_hold_fit.
- Pass-within-3 s by zone: def 0.629 / mid 0.703 / att 0.596 —
  middle third moves it quickest, attacking third holds longest
  against set defenses. Same table, same test.

## What the fit banked

Labels, window, and sample behind the calibration above: banked by
`scripts/label_retention.py` from 7 raw IDSSE matches (same run as
gates 4–5, next-event lookups added). Rows are dicts with join keys.
Cut off — dropped, not censored — when tracking gaps, the half ends,
or no next event is found: the pool is complete intervals only, same
reception-conditioning as gates 4–5. No survival modeling; the
censoring question is deferred with the n to deserve it.
- Three exits, stratified not pooled: pass / loss / stoppage reported
  separately per zone (the +3 s rate is pass-only; loss and stoppage
  are context columns, not pooled into the mean). Averaging a tackle
  with a pass repeats the constructed-label problem in reverse —
  erasing real boundaries instead of inventing them.
- Next-event lookup per match: pass_idx ordering is necessary but not
  sufficient — consecutive banked rows aren't consecutive possession
  events (failed receptions drop rows). Link by same-match +
  next-timestamp with gap handling; drop pairs across tracking gaps.
- Minimum n: 1,160 intervals, continuous times — SE on a mean, same
  comfort as gate 5.
- Sources: IDSSE only for the fit. Same replication ladder as gates 4–5.

## Deleted before fitting

- GRNN joint action models: can't run on banked pools (no weights,
  no code), and the question they answer (which of 11 actions, when)
  isn't the attempt gate. Cited as method prior, never fitted.
- EPV as attempt value: prices states, not durations. Different gate.

## Edge

Conditions on control, which conditions on arrival, which conditions
on attempting the receipt — the attempt being timed is itself
conditional, and the full whether stays outside. Deployment caveat
carries forward: fit on pre-instrument hold durations drifts once
players optimize tempo — recalibrate on post-deployment sets.
