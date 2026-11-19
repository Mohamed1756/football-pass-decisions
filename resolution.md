# Resolution

(Research note for Football Passing Chain — how the freeze resolved
after control. Deltas banked on 1,160 receptions with +3 s windows.)

The freeze gate 3 scored, three seconds later: press access
and compactness at receipt vs +3 s. Resolution describes shape 3 s
after receipt; it doesn't rate it — no good/bad, no value
function, no table link.

## What it measures

- Press access: nearest-opponent distance to ball, after minus before.
- Compactness: mean defender-to-ball distance, after minus before.

Banked on all 1,160 rows (full +3 s windows), same
label_retention.py run, forwards. Pinned in test_structure_fit.

## Calibration (by zone x control)

- Controlled receptions read tighter on average everywhere: press
  access −1.40/−1.08/−2.52 (def/mid/att), compactness
  −2.31/−0.22/−2.19. Value lives in the right tail: a quarter to a
  third of controlled receptions loosen press access (P(>0)
  0.36/0.35/0.26; P(>2 m) 0.16/0.21/0.12). Pinned in test_structure_fit.
- Failed controls read looser in mid (+0.44 press, +0.59 compact),
  but the mean hides the skew: mid-failed median is −0.08, a near
  coin-flip (P(>0) = 0.478) with a 24 m max. Tail-driven on both
  sides.
- Window artifact: 65% of rows have their next event inside the +3 s
  window, so the delta reads shape after the next action started.
  Δpress mean is −0.71 when hold < 3 s vs −1.06 when hold ≥ 3 s —
  convergence over 3 s is partly the window, not the pass. Window
  options needing raw (shorten to +1.5 s, censor at next event) wait
  for the re-bank; the +3 s deltas stay, relabeled descriptive.
- Open-man counts cut on both sides: +0.01 to +0.21 everywhere —
  repositioning without separation, noise with a name.

## Killed paths

- Shot, progression, binary loosened/not: see git history (rare-event,
  constructed-label, reintroduces path-B trap respectively).

## Sources

never pools. 360 excluded (no time axis). Metrica mechanism tests only.

## Edge

Conditions on control, which conditions on arrival, which conditions
on attempting: three selection gates upstream. Resolution deltas are
E[shape(+3 s) − shape(0) | controlled | arrived | attempted] —
descriptive shape change, not what the pass did. Deployment caveat
carries forward: fit on pre-instrument shape-changes drifts once
passers optimize for loosening — recalibrate on post-deployment sets.
