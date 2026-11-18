# Resolution

(Research note for Football Passing Chain — how the freeze resolved
after control. Deltas banked on 1,160 receptions with +3 s windows.)

The freeze gate 3 scored, three seconds later: press access
and compactness at receipt vs +3 s. Resolution describes what
the pass did to shape; it doesn't rate it — no good/bad, no value
function, no table link.

## What it measures

- Press access: nearest-opponent distance to ball, after minus before.
- Compactness: mean defender-to-ball distance, after minus before.

Banked on all 1,160 rows (full +3 s windows), same
label_retention.py run, forwards. Pinned in test_structure_fit.

## Calibration (by zone x control)

- Controlled receptions tighten structure everywhere: press access
  −1.40/−1.08/−2.52 (def/mid/att), compactness −2.31/−0.22/−2.19.
  The average completed pass does not loosen anything — defense
  converges on the ball over 3 s. Value lives in the right tail.
- Failed controls loosen mid (+0.44 press, +0.59 compact): the ball
  is already moving the other way.
- Open-man counts cut on both sides: +0.01 to +0.21 everywhere —
  repositioning without separation, noise with a name.

## Killed paths

- Shot, progression, binary loosened/not: see git history (rare-event,
  constructed-label, reintroduces path-B trap respectively).

## Sources

never pools. 360 excluded (no time axis). Metrica mechanism tests only.

## Edge

Conditions on control, which conditions on arrival, which conditions
on attempting: three selection gates upstream. Resolution rates
are E[ΔS | controlled | arrived | attempted]. Deployment caveat
carries forward: fit on pre-instrument shape-changes drifts once
passers optimize for loosening — recalibrate on post-deployment sets.
