# Structure-delta

(Research note for Football Passing Rank — how the freeze resolved after
control. First fit banked on 1,160 labeled receptions with +3 s windows.)
How the freeze resolved: the pass either unbalances the defensive
structure (space opens, the next freeze is easier) or it doesn't
(structure resets, next freeze as hard or harder).

`E[ΔS | zone]` with control as covariate — six cells (zone ×
controlled True/False), not a controlled-only mean. Uncontrolled
rows are scored, not dropped: a lost ball hands the opponent a
different structure, and the contrast (tighten-on-control vs
loosen-on-turnover-mid) is the finding. The three upstream gates
still condition the population (arrived | attempted); control is
the covariate gate 5 splits on, not a filter.

Clocks start at receipt (the measured reception frame), not at the
pass event: gate 5 conditions on control, so its t=0 is where
control is decided. The window is receipt+3 s: next-pass timing on
IDSSE (n=312 receptions, one match) puts the median next pass at
2.4 s (q25–q75 1.4–5.0), so 3 s lands mid-reorganization — after
the next action starts forming, before the shape settles.
Cited from one match, not banked; sensitivity at ±1 s untested.
Rows without a full +3 s window are dropped (same
reception-conditioning as gate 4).
Three candidate components, all pure frame arithmetic on tracking
both sides of reception:

- Press access: nearest-opponent distance to ball at receipt+3 s
  minus at receipt. Positive = the pass broke pressure.
- Choice-set size: count of teammates with separation > 5 m from
  their nearest opponent at each freeze, after minus before. The
  5 m is a borrowed prior, not a fit: median marking distance on
  the banked 1,160 is 5.64 m (≤5 m: 0.42 control, >5 m: 0.65),
  but that quantity is nearest-opponent-to-ball, not
  nearest-opponent-to-each-teammate as counted here. Same scale,
  different measurement — sensitivity untested, refit when n allows.
  A frame property, not a margin call: gate 3's margin needs a
  passer the +3 s freeze doesn't have. Positive = more options created.
- Compactness: mean defender-to-ball distance (or hull area), after
  minus before. Positive = shape stretched.

## Calibration (1,160 receptions with +3 s windows, by zone x control)

- Controlled receptions tighten structure everywhere: press access
  −1.40/−1.08/−2.52 (def/mid/att), compactness −2.31/−0.22/−2.19.
  The average completed pass does not loosen anything — defense
  converges on the ball over 3 s. Value lives in the right tail,
  not the mean.
- Failed controls loosen mid (+0.44 press, +0.59 compact): the ball
  is already moving the other way. Def/att failures still tighten
  (−0.03/−0.67 press) — edges stay compact even in transition.
- Open men barely move anywhere (+0.01 to +0.21): the +3 s window
  repositions bodies more than it creates separation. Weakest of
  the three components; candidate for cutting if pose data doesn't
  rescue it. Pinned in test_structure_fit.

## Why not shot, why not progression

- Shot (P(shot | control, zone)): estimated ~3% base rate on 1,160
  receptions is ~35 positives — an estimate, not a count: the loader
  never parsed shot Plays and the banked pools carry no shot labels,
  so the rate cannot be computed here. At that n any zone split sits
  inside its own error bars; and the path drags the project into
  shot-quality modeling where it adds nothing. Killed: rare-event
  (estimated) plus scope.
- Progression (P(advance | control, zone)): fittable base rate, but the
  label is constructed — box entry, +x meters, shot-in-window are all
  choices, and the fit inherits the definition's arbitrariness. Killed:
  constructed-label.
- Structure-delta is observable wherever tracking is complete — ball
  plus all 22 at receipt and +3 s. Gate 4's window already drops ~2/3
  of candidate passes on missing frames; expect 60–70% coverage of
  completions here, less of all passes. Needs no new sources, and is
  designed to feed gate 0 once specified — a recurrence, not a
  terminus. Killed paths documented so nobody re-proposes them.

## What the fit banked

Labels, window, and sample behind the calibration above: banked by
`scripts/label_retention.py` from 7 raw IDSSE matches (same run as
gate 4's labels, +3 s lookups added). Rows are dicts with join keys
plus reception position and three deltas.
- Zone map: reception zone, thirds (def/mid/att); finer only if n
  carries it (~115/bin rule from gate 4).
- Minimum n: 1,160 continuous outcomes (means, not rates) — SE on a
  mean far kinder than gate 4's rate SEs. Fittable where P(shot) wasn't.
- Sources: IDSSE only for the fit (25 fps optical + ball; only source
  with frames, outcomes, and precision). SkillCorner broadcast replicates
  but doesn't pool (10 fps extrapolated frames, delta-scale noise).
  360 never (one frozen frame). Metrica mechanism-tests only.

## Deleted before fitting

- Any threshold on ΔS as "success": the delta is continuous; a binary
  loosened/not split would reintroduce the constructed-label problem
  path B died of.
- Shot chains as gate 5: see above.

## Edge

Conditions on control, which conditions on arrival, which conditions
on attempting: three selection gates upstream. Structure-delta rates
are E[ΔS | controlled | arrived | attempted]. Deployment caveat
carries forward: fit on pre-instrument shape-changes drifts once
passers optimize for loosening — recalibrate on post-deployment sets.
