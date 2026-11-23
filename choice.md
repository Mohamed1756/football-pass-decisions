# Choice

(Research note for Football Passing Chain — which outlet gets picked,
given the freeze. First fit banked on 171,440 banked choice rows.)

The choice is banked on every 360 pass: one row per pass (chosen
outlet's rank, margin, outcome). Denominator disclosed, not
reproducible in-repo: per the calibration analysis, 740
recipient-less WC2022 passes were dropped pre-pool (the five-league
pre-drop total is not in-repo), in-frame counts never banked.
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
- Unconditioned on choice-set size in the five-league pool: rows carry
  (margin, rank, complete) with no n_outlets. Resolved separately on
  LaLiga 2020/21 360 (26,906 in-frame sets, scripts/label_360_choice_sets.py):
  top-2 is 0.674 overall and 0.673 on ≥3-outlet sets — the mechanical
  small-set mass is 105 rows, moving the headline 0.001. The 0.677
  upper bound was conservative by construction; the measured mass is
  negligible because tiny sets are rare (91 two-outlet sets at 1.00).
  Pinned in test_choice_sets_360. In-frame sets average 7.3 outlets vs
  10.0 full-pitch IDSSE — levels stay non-comparable, shapes compare.

## What the fit banked

Counted from frozen_five_leagues.pkl: rows are dicts with (margin,
rank, complete) — no passer IDs, no zones. 360 for the fit;
IDSSE keeps the passer-trait null. Deleted: GRNN joint models
(can't run), passer-trait models (nulled, retry at triple digits),
zone/spread splits (don't bin what isn't there).

## Load conditioning (IDSSE full sets, n=1,160; LaLiga 360 in-frame, n=26,906)

Unblocked by scripts/label_choice_sets.py: every tracked teammate
scored as an outlet at the pass frame (frozen margins, passer
excluded by name lookup with a nearest-mate fallback, 136/1,160 rows,
counts pinned per match). Mean set: 9.9 outlets, 8.6 viable, effective
7.1. Chosen rank-0 rate 0.216 on full-pitch sets — below the 360
in-frame headline, different denominator, not comparable (joins
table in pooled README).
Rank-0 share by viable size: 0.53 (≤7, n=240) → 0.18 (8) → 0.16
(9) → 0.08 (≥10, n=378); by effective options: 0.65 (≤5) → 0.28 →
0.11 → 0.09 (>9). Both strictly monotone. Passers beat uniform at
low load and fall to it at high load. Pinned in
test_choice_sets_table. Single environment (7 matches, short-pass
selected): the gradient is established, its portability is not.
Replicated on LaLiga 2020/21 360 (26,906 in-frame sets, nearest-to-end
recipient mapping, verify p50 3.8 m): rank-0 share 0.47 (≤7, n=17,630)
→ 0.37 (8) → 0.33 (9) → 0.14 (≥10, n=210), monotone. Same shape, higher
floor — in-frame sets are smaller and safer (chosen rank-0 0.431,
matching the 0.41–0.44 headline). Pinned in test_choice_sets_360.
## Luce-McFadden tried, not banked

Single pooled β over frozen margins (`scripts/fit_choice_beta.py`,
read-only on the pool): β = 0.99, sign correct, leave-one-match-out
range 0.96–1.05, beats the uniform null by 520 nats. Fails its own
bar: predicted rank-0 share 0.47/0.39/0.35/0.32 across the viable-size
bins against observed 0.53/0.18/0.16/0.08 (tolerance was ±0.06), and
parameter-free linear-p wins out-of-sample (−2,037 vs −2,135 nats on
1,159 viable-chosen rows). One margin-sensitivity cannot produce the
observed steepness. No `choose_prob`, no banked β; the script stays as
the negative result. Split-β follow-up (fit on extreme bins only):
β_low = 1.44 vs β_high = 0.69, ordered as predicted, beats pooled
out-of-sample (−2,120 vs −2,139) — but the ±0.06 gradient bar still
fails on three bins (middle bins reuse pooled β by design; big-set
behavior sits near uniform, which no positive β reaches). Direction
confirmed, magnitude incomplete. Uniform-mixture follow-up
(`scripts/fit_choice_mixture.py`: shared β + per-bin uniform weight):
all four λ fit to 0.000, collapsing to pooled softmax — MLE over chosen
outlets refuses the uniform component because chosen outlets are usually
high-margin, while the miss lives in the aggregate rank-0 pattern, a
moment the likelihood doesn't see. Three behavioral forms tried, gradient
behavior sits near uniform, which no positive β reaches. Modeling
stops here: the empirical gradient stands, the mechanism behind
big-set randomness is unidentified on margins alone.
Value-Luce (`scripts/fit_choice_value.py`, same bars, identical 937
rows and folds, attack sign from territory with a 3 m gate): β = 3.50,
gradient 0.33/0.27/0.25/0.24 vs observed 0.46/0.19/0.12/0.08 — fails
all four bins; LOO value −1,880 loses to split-softmax (−1,684) and
probabilistic model. Mechanism direction right, model wrong. No
banking; the stepper interface is demonstrated in-script only.
Replicated on LaLiga 360 (`scripts/evaluate_360_choice.py`, same bars,
16,312 attack-mapped rows): β = 10.31, gradient pred 0.40/0.32/0.29/0.46
vs obs 0.40/0.28/0.27/0.09 — first three bins inside ±0.06, the ≥10 bin
fails on n=124. Identity reverses here: value-rank-0 0.356 vs
margin-rank-0 0.429 (IDSSE read 0.193 vs 0.104). LOO again goes to
linear (−25,183 vs −26,435). Verified-subset retest (`--verified-only`,
n=10,538, chosen within 5 m of the end point): identity value 0.358
vs margin 0.441 — cleaning attribution widens margin's lead instead
of restoring value's. The misattribution hypothesis is rejected; the
identity edge was IDSSE-specific (live tracking or full-pitch sets),
not general. No banking; the form stays rejected on both pools.
Gate-2 modeling closes: descriptive gradient stands on both pools,
identity unidentified, loop stepper unbuilt for cause.

## Branch credit readout (descriptive, no fit)

`scripts/choice_credit.py` scores every freeze end-to-end off banked
pools + raw positions: per viable outlet value (frozen replay,
±0.001 consistency gate), A-credit = value(chosen) − mean(viable),
regret = best − chosen, B-residual = controlled − fitted(cushion),
plus hold, delta, marking and zone context. n = 937 (attack-mapped;
223 rows dropped on 6 ambiguous territory cells, counted).
Mean credit by load: 0.138 (≤7) → 0.082 → 0.063 → 0.032 (≥10);
mean regret rises 0.093 → 0.168 → 0.194 → 0.245. B-residual mean
+0.035 (curve calibrated on this subset). Identity: value-rank-0
0.193 vs margin-rank-0 0.104. Definitions pinned in
test_choice_credit; aggregates printed by the script.

## Edge

Conditions on the freeze (gate 0 describes it) and precedes arrival
(gate 3 scores the chosen outlet). Deployment caveat carries
forward: fit on pre-instrument choices drifts once passers optimize
the margin — recalibrate on post-deployment sets.
