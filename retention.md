# Retention

(Research note for Football Passing Rank — the mechanism behind keeping
the ball after arrival.)

Control given arrival: the receiver has beaten the press to the
intercept (`margin > 0`). Keeping the ball is a second race with the
same shape as the first: the receiver needs `touch_need` seconds to
control it, the nearest presser needs `t_disrupt` seconds to arrive
and contest it. Retention holds iff `touch_need < t_disrupt`, both
clocked from the reception instant. Concretely: `touch_need` is the
fitted touch curve's job (cushion→time), and `t_disrupt =
marking_dist / presser_close_speed` with the presser's gated closing
speed where tracking carries it, sprint-cap fallback where it doesn't.
Wrong-able like everything else — the fit's job is to break it.

`P(control | cushion, marking)` — cushion is the post-touch time
left (`post_cushion_s`), marking is the presser's live distance at
the reception instant (advanced by gated velocity over `t_ball`
where tracking carries velocities; frozen at t=0 only where it
doesn't — convention inherited from arrival, portability cost named
below). Both already computable; neither yet calibrated against a
touch label.

- The mechanism is multiplicative until the fit says otherwise:
  `P(control) = f(cushion) × g(marking)` with f the touch curve and
  g a marking discount (1.0 alone at the intercept, decaying as the
  presser closes). Independence is the null to beat, not a truth —
  the fit tests it by comparing against a joint form.

## Calibration (1,160 labeled touches, 7 IDSSE matches)

- Winner: shifted exponential, cushion only —
  P(control) = 1 − e^(−0.40·(cushion+1.50)), floored at 0 below −1.50.
  NLL 782.6 vs null 793.3 (dNLL 10.7); assumed logistic (15, 0.15)
  loses to the null by 2412. The exponential's original sin was
  zero-at-zero: control at non-positive cushion is 0.44, and the
  shift absorbs exactly that.
- Control by pooled cushion-decile (own tenths): 0.43/0.43/0.48/
  0.49/0.58/0.64/0.62/0.64/0.71/0.67, monotone rising to q9 with a
  q10 dip on n=115 — noise, same tail pattern as gate 3. Fitted
  means track within ~0.11 throughout (worst at q1, where the floor
  binds). Pinned in test_retention_fit.
- Marking residual confirmed but unscored: within-cushion-band splits
  separate 0.36 vs 0.53 (tight) to 0.61 vs 0.75 (loose), yet the
  bivariate discount buys only dNLL 1.2 — real but below the bar.
  Revisit at n≥5,000 or pose-derived facing; needs dNLL ≥ 10 to earn
  its parameters. Until then the composition carries marking, never
  fits it.

## What the fit needed

Labels, window, and sample behind the calibration above:
- Touch labels: controlled / lost at receipt +1 s, binary. The third
  label ("contested") is dropped: nothing in tracking + events draws
  that boundary with a rule, so the fit is binary and the note stops
  pretending otherwise. Window is +1 s because Spearman fits ~95%
  control within 1 s (λ = 4.3/s) — the window is cited, not invented.
  IDSSE Evaluation still marks the pass, not the touch; the label
  does not exist in any banked pool. Nothing fits without it: one
  label definition, applied to the 1,160 measured receptions.
- Facing floor: unknown facing is taxed twice (0.25 s onto `t_press`,
  plus 0.25 s onto reception latency) — documented bias, not measured
  cost. A 0.39 s placeholder mean was tried and cut when the fit won
  on 0.25-floor cushions. Retention uses arrival's cushion as-is.
- Marking at receipt, not at decision: `marking_dist_m` is frozen at
  t=0 by arrival's convention (portability over precision, documented
  pro-receiver bias). Live marking stays unscored: the bivariate
  discount buys dNLL 1.2 on 1,160 rows — real but below the bar.
  Revisit trigger: n≥5,000 labeled touches or pose-derived facing,
  whichever first; the joint form needs dNLL ≥ 10 on the same pools
  to earn its parameters. Until then, frozen marking is carried for
  display, never fit.
- Minimum n: 1,160 binary labels over cushion deciles is ~116/bin
  (SE ≈ 0.05 at p = 0.5) — workable for curve shape. Bivariate with
  a marking split halves it (~58/cell, SE ≈ 0.07): enough to test
  the discount, not to fit it finely. The tight-quintile team splits
  (Perth 0.318 vs City 0.140) motivate but cannot validate — no
  labels, same margins at two gates. Team and per-receiver splits
  wait behind the pooled fit, same as gate 3.

## Facing: measurable, but coarsely

- `facing_rad` is set in tests only; all three loaders emit unknown, so
  the whole hip-pivot path has zero real-data coverage. The unlock is
  inside a source already cited: SkillCorner ships 3D body pose (29
  joints) for 2 matches — shoulders+hips normal gives `facing_rad`,
  and the `facing_source` provenance field already exists to carry it.
- Error budget caps the use: pose→orientation validates at 27.7°
  median error vs EPTS (Arbués-Sangüesa et al., Barça/UPF
  2020) — same width as the 35° open-hip boundary. Coarsen to
  open/needs-turn binary until pose error drops; the full curve on
  noisy facing is fiction with error bars.
- 360 carries ordering only: no fitted retention levels apply (live
  marking uncomputable, double floor uncorrected there) — cushion
  rank still orders, same portability argument as gate 3.

## Deleted as unverifiable

- Race machinery (`touch_need_s`, `disrupt_time_s`, `RetentionMargin`,
  `retention_margin_s`): the fit voted direct curve (exp-shift NLL
  782.6) — the second race stays a motivating picture, not code.
- 0.39 s unknown-facing mean: cut when the fit won on 0.25-floor
  cushions. Rule: never mutate a fitted gate's inputs to fit an
  unfitted one; each gate owns its latency.
- Any threshold on the old assumed logistic: absolute value was never
  calibrated, ordering only.
- Named null the fit had to beat: cushion-only logistic, then
  cushion-only exponential, then either with the marking discount.
  Logistic rung lost (NLL 3205 vs null 793); exponential rung won
  (782.6 vs 793.3). Marking-discount rung pending at dNLL ≥ 10.

## Edge

Conditions on arrival, which conditions on attempting: two selection
gates upstream, both stated in arrival.md. Retention rates are
P(control | arrived | attempted) — not P(control | pass played).
Deployment caveat carries forward: fit on pre-instrument first touches
drifts once receivers train to the cushion.
