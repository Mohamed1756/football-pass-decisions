# Choice

(Research note for Football Passing Chain — which outlet gets picked,
given the freeze. First fit banked on 171,440 banked choice rows.)

The choice is banked on every 360 pass: one row per pass (chosen
outlet's rank, margin, outcome). Denominator disclosed, not
reproducible in-repo: per the calibration analysis, 740
recipient-less passes were dropped pre-pool, in-frame counts never
banked.
P(choose rank r): the choice-share curve over ranks, pooled — the
pool fits, not the person (passer-trait null stands at corr 0.01–0.02).
## Why pooled now, hierarchy later

- Pooled: no new source, no new labels, no raw needed. Zone and
  spread splits wait for a re-bank with pass grouping.
- Hierarchy needs passer IDs the pool doesn't carry, and 200+
  passers n≥5 (rule of thumb vs the ICC ≈ 0.03 floor) where IDSSE
  has 51. The re-bank that adds IDs also adds n_outlets per row,
  unlocking set-size conditioning in the same pass — one blocked
  task, not two.
- Cross-source pooling dropped: a provider term where one source
  carries rate and the other carries dynamics absorbs the
  difference it should explain.

## Calibration (171,440 choices, by league)

- Rank-0 choice 0.41–0.44 everywhere (WC2022 0.436, n=18,103);
  curve falls to a pooled tail (rank 7+: 0.006–0.010, n<300 per
  league — same pattern as gates 3–4). Top-2 ranks take ~0.68 pooled
  (0.677; LaLiga lowest at 0.654). Dropping the rank-7+ tail and
  renormalizing moves top-2 by +0.004 to +0.006 per league.
  Pinned in test_choice_shares.
- Unconditioned on choice-set size: rows carry (margin, rank,
  complete) with no n_outlets, and 1- and 2-outlet sets take top-2
  mechanically. Direction is identified even though the mass is not:
  0.677 is an upper bound on the ≥3-outlet top-2 share — any
  mechanical small-set mass pulls it down. Removing all rank-1 rows
  gives 0.571, but that is an extreme scenario, not a bound — it
  assumes every rank-1 row is a mechanical small-set take and no
  rank-0 row is, against the margin-preference direction. The
  small-set mass is unidentified from this pool, so the headline
  stays unconditioned until the re-bank.

## What the fit banked

Counted from frozen_five_leagues.pkl: rows are dicts with (margin,
rank, complete) — no passer IDs, no zones. 360 for the fit;
IDSSE keeps the passer-trait null. Deleted: GRNN joint models
(can't run), passer-trait models (nulled, retry at triple digits),
zone/spread splits (don't bin what isn't there).

## Edge

Conditions on the freeze (gate 0 describes it) and precedes arrival
(gate 3 scores the chosen outlet). Deployment caveat carries
forward: fit on pre-instrument choices drifts once passers optimize
the margin — recalibrate on post-deployment sets.
