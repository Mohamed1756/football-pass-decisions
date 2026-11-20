# Pooled evidence: what the files are and what regenerates them

Three reproducibility classes — "regenerate from the loaders" below
means you could write a script, not that one is banked. Exactly one
pool-writing command exists in-repo (`scripts/label_retention.py`).

- Reproducible by command: `idsse_retention_labeled.pkl` only, via
  `python3 scripts/label_retention.py` given the 7 raw matches at
  `/tmp/idsse_raw` (HuggingFace `pysport/idsse-data`, re-downloadable;
  ~2 min, 400 MB XML, not vendored). Run on demand, not in CI.
- Loader-startable but unscripted: the six `idsse_*` measurement pools,
  the three `skillcorner_*` pools, and `value_choice_by_passer.pkl`.
  Loaders exist in `src/io/` (plus the repo test fixtures' hand
  slices), but each pool also needs unbanked logic on top (team join +
  live-presser margins, full-pitch choice-set aggregation,
  drag-rematch extraction): no banking script is banked for any of them.
- Frozen reference inputs: `frozen_five_leagues.pkl` — no StatsBomb
  360 loader exists here. Kept auditable by the counts and edge
  values printed below; LOLO pins the artifact, not a regenerable
  pipeline, so a 360 re-cut is impossible in-repo.

The scoring rule that bins everything (WC2022 edges) is the literal
`DECILE_EDGES_S` in `src/models/pressing/calibration.py`.

| File | n | Backs |
|---|---|---|
| `frozen_five_leagues.pkl` | 171,440 dicts by league (margin, rank, complete) | fig1 five curves, LOLO-monotone in every fold (52–138x refit gradients; endpoints d1 ≈0.20 men / 0.276 women, d10 ≤0.005). **Frozen 360 input: no loader in repo.** Counts: wc2022 41,561; euro2020 33,761; laliga 28,694; euro2024 34,617; wwc2023 32,807 |
| `skillcorner_frozen_live.pkl` | 14,814 ×2 (margin, outcome) | fig1 sixth line, first (heuristic) cut. Superseded by the targeted pool below |
| `skillcorner_targeted_frozen_live.pkl` | 14,822 ×2, targeted receivers | **Canonical broadcast pool.** Pooled-decile d1 0.245 frozen / 0.221 live (same shape, noisier tight top); supersedes heuristic version |
| `skillcorner_team_margins.pkl` | 14,822 live-presser margins keyed (match, side) → 13 clubs after the match_teams.json join (fig3/table n=13,122 is the plotted labeled-pass subset — recount before reusing) | fig3 team fingerprints (join match.json for names) |
| `idsse_ball_flights.pkl` | 2,246 (t, dist) segments | Coulomb wins short-window fit (RMSE 0.035 m) |
| `idsse_reception_speeds.pkl` | 1,128 (dist, v0, t_true) | Drag rematch grid (Coulomb-22 wins) |
| `idsse_rematch_656.pkl` | ndarray (656, 3) of (dist, v0, t_true) — not a list of tuples like its siblings | Same grid, post-cleaning subset |
| `idsse_measured_all_1160.pkl` | 1,160 (margin, outcome) | Full measured pool (canonical; pooled-decile d1 0.40 → d10 0.01) |
| `idsse_measured_live.pkl` | 673 (margin, outcome) | First-3-matches cut cited in earlier drafts |
| `idsse_pooled7.pkl` | 631 (margin, outcome) | Same, alternate cut; kept for audit |
| `value_choice_by_passer.pkl` | 124 passers: name → [n, rank0_choices, value_choices, completions, total_outlets] (51 with n≥5 drive the null: rank-0 choice 0.00–0.25, completion 0.60–1.00, value/completion corr 0.02) | Value-added null |
| `idsse_retention_labeled.pkl` | 1,160 dict rows: match/target/passer keys, margin, t_ball, cushion, marking, controlled, recept x/y, delta press+compact, pre press+sep-vel, hold duration+exit. 659 controlled, 1,159 with full −5 s, all with +3 s. Banked by `scripts/label_retention.py` from 7 raw matches (HuggingFace `pysport/idsse-data`, re-downloadable). Keys: `recept_x_m`, `recept_y_m`, `delta_press_m`, `delta_compact_m`, `pre_press_m`, `pre_sep_vel`, `hold_s`, `hold_exit` | Gates 4–5 + freeze + attempt: shifted exp wins (NLL 782.6 vs null 793.3); structure press −0.83 / compact −0.72; hold median 2.16 s; pre-freeze press 5.5–7.2 |

Superseded cuts are marked, not deleted: early notes cite their numbers.

## Figure provenance

No script in this repo generates the figures: they are frozen binaries.
`fig1_decile_curves.png` plots the frozen-edge table `reproduce.py`
prints for the five 360 curves; its broadcast sixth line is the
superseded heuristic cut (`skillcorner_frozen_live.pkl`, n=14,814,
frozen-edge d1 1946/8642 = 0.225), kept as published — the canonical
targeted cut (n=14,822, d1 1948/8645 = 0.225) agrees to ≤0.003 across
deciles (1e-4 at d1, max 0.0029 at d9), so the plotted line stands. `fig3`, `fig5`, `fig6`, `fig7` are
hand-built SVGs/PNGs from the commits named in git history (`cef4edf`
started fig1 as a tracked SVG; `4b7aeef` rendered the PNG; `f843448`
added fig7). Uneditable without the source data + a plotting script:
to change a figure, rebuild it from the pool it cites and bank the
script in `scripts/` in the same task. Until then, captions describe
what is plotted, not what a rerun would plot.
## Binning rule, stated once

Headline gradient figures (arrival.md, fig1) use **pooled deciles**:
each pool is split into its own tenths, so d1 always holds that pool's
tightest 10%. Cross-pool comparison on common ground uses **frozen
WC2022 edges** (`DECILE_EDGES_S`): the same absolute margin, whatever
share of each pool falls in it. `scripts/reproduce.py` prints the
frozen-edge table (portable seconds); the headlines print the pooled
table (portable shape). Both binnings, both labeled — never one
presented as the other.

## Joins: what survives

Cross-league arrival comparisons survive: one measurement (360 frozen
shape), one edge set, both binnings labeled. Every IDSSE↔360 level
transfer fails; only ordering transfers.

| Comparison | Join needed | Verdict |
|---|---|---|
| rank-0 choice 0.41–0.44 (360, in-frame sets) vs 0.00–0.25 (IDSSE, full-pitch, 8.7 outlets/pass) | common choice-set definition | Not joinable from banked pools. Uniform baselines differ mechanically (~1/3 360 per the calibration analysis, unverifiable from banked rows which lack set sizes, vs 1/8.7 IDSSE); IDSSE passers sit below uniform, 360 above. Unidentified until set definitions match. |
| control levels (IDSSE n=1,160) on 360 margins | touch labels on 360 (don't exist) | Forbidden by retention.md, enforced by `run_outlet`'s source flag. Ordering-only on 360. |
| 360 decile edges on IDSSE margins | same-n, both binnings labeled | Survives as labeled comparison (`reproduce.py` prints it). `run_outlet`'s risk field is out-of-scale on measured inputs (see pipeline docstring). |
| "passers complete 60–100%" vs control 0.43–0.71 | complete × controlled join | Joinable: P(control \| complete) = 0.596, pinned in test_retention_fit. Prose mixing the labels uses the join. |
| loop +0.10 vs claimed conditioning | previous-controlled filter | r → 0.017; the published number is not the claimed estimand (freeze.md). |
| resolution ΔS vs hold | next-event timing | 65% window overlap; see resolution.md (Q6). |

## Selection, stated once

The IDSSE 1,160 denominators are short-pass-selected by construction:
`_reception_point` takes the first ball position within 2 m inside 1 s
of flight, so banked t_ball tops out at 1.00 s (~21 m). Retention and
hold fits inherit that truncation alongside arrival.
## Monitoring / recalibration triggers

Every gate note promises recalibration on post-deployment sets. This
is the spec that promise points at. On any new pool recompute:
(a) rank-0 choice share, (b) frozen-edge d1 incompletion rate,
(c) control rate. Alert thresholds (operational choices, not derived):
rank-0 share shifts >0.05 absolute, d1 rate shifts >0.03 absolute,
control rate outside the banked match-clustered 95% CI. Crossing a
threshold means refit before trusting levels; ordering claims survive
threshold breaches unless the monotone shape itself breaks (see LOLO).
Pre-deployment Goodhart testing is impossible by construction — no
pool exists of passers optimizing this instrument — so the caveat
stays prose until the first post-deployment pool lands. No monitor
script is banked: it gets written against that pool, not this one.
