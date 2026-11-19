# Attempt

(Research note for Football Passing Chain — how long the ball sticks
before the next action. First fit banked on 1,160 intervals.)

The unplayed ball is unobserved: no event+tracking dataset records
the pass not played. So gate 1 does not model the decision — it
models its duration. Given receipt, how long until the next pass
attempt or loss?

`E[T_hold | zone]` as banked (all 1,160 receptions); `E[T_hold |
control, zone]` controlled-only (n=659) reported alongside. The clock
starts at receipt (same t=0 as gate 5); the freeze is context, not condition.
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
  possession interval ending in pass/loss on IDSSE events +
  tracking. Controlled-only timing matches every other gate
  (controlled | arrived | attempted); the banked all-reception table
  is reported alongside. The true whether for non-receipt moments
  stays unbuilt and named.

## Calibration (1,160 intervals, by zone x exit)

- Median hold 2.16 s overall (q25 1.36, q75 3.92; 2.40 s controlled-only):
  mid releases fastest in both conditionings (1.96 all, 2.24 controlled);
  all-reception edges read def 2.52, att 2.34, but controlled-only att
  holds longest (def 2.56, att 2.68). Pass exits dominate everywhere
  (958/1160); loss is the minority exit in all three zones (57/89/56);
  stoppage is a structural zero (loader visits Play elements only).
  Pinned in test_hold_fit.
- Pass-within-3 s by zone: def 0.629 / mid 0.703 / att 0.596 —
  middle third moves it quickest under both conditionings (controlled:
  0.62 / 0.664 / 0.574). Same table, same test.
- Mean 6.74 s is annotation contamination, not duration: max hold
  783 s, 61 rows above 30 s. Median is robust (2.16 down to 2.04
  trimming above 30 s); the mean and exit shares are not trustworthy
  as possession durations.

## What the fit banked

Labels, window, and sample behind the calibration above: banked by
`scripts/label_retention.py` from 7 raw IDSSE matches (same run as
gates 4–5, next-event lookups added). Rows are dicts with join keys.
Cut off — dropped, not censored — when no next annotated event is
found. No tracking-gap, half-boundary, or team filter: long tails are
annotation gaps, not possessions. No survival modeling; the censoring
question is deferred with the n to deserve it.
- Two exits observed, stratified not pooled: pass / loss reported
  separately per zone (the +3 s rate is pass-only; loss is a context
  column, not pooled into the mean). Stoppage is a structural zero —
  the event loop visits Play elements only, so whistle events never
  enter the pool. Averaging a tackle with a pass repeats the
  constructed-label problem in reverse — erasing real boundaries
  instead of inventing them.
- Next-event lookup per match: pass_idx ordering is necessary but not
  sufficient — consecutive banked rows aren't consecutive possession
  events (failed receptions drop rows). Link by same-match +
  next-timestamp; pairs across tracking gaps are not dropped, so a
  "pass" exit can be the opponent's pass after an unannotated turnover.
- Minimum n: 1,160 intervals, continuous times — SE on a mean, same
  comfort as gate 5.
- Sources: IDSSE only for the fit. Same replication ladder as gates 4–5.

## Deleted before fitting

- GRNN joint action models: can't run on banked pools (no weights,
  no code), and the question they answer (which of 11 actions, when)
  isn't the attempt gate. Cited as method prior, never fitted.
- EPV as attempt value: prices states, not durations. Different gate.

## Edge

Banked over all receptions; controlled-only timing (n=659) matches the
gate conditioning (control, which conditions on arrival, which
conditions on attempting the receipt) — the attempt being timed is
itself conditional, and the full whether stays outside. Deployment caveat
carries forward: fit on pre-instrument hold durations drifts once
players optimize tempo — recalibrate on post-deployment sets.
