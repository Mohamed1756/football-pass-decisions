"""Pinned retention fit: first contest on banked labels, exact counts.

Gate 4 slice 3 result. The assumed logistic (k=15, mid=0.15) is not a
fit — it loses to the null by 2412 NLL. The winner is a shifted
exponential in cushion; marking adds a small residual gain.
Winner params live in mechanism (single home); this file pins NLLs.
"""

import math
import pickle

from src.models.retention.mechanism import FIT_C0, FIT_LAM, fitted_control_prob


def _touch_curve_logistic_null(cushion_s: float) -> float:
    """Assumed logistic (k=15, mid=0.15): the null the winner beat.

    Lives here, not in mechanism: its only caller is the assumed-NLL
    pin below. Production curve is fitted_control_prob.
    """
    return round(1.0 / (1.0 + math.exp(-15.0 * (cushion_s - 0.15))), 4)


RETENTION_LABELED_PATH = "data/pooled/idsse_retention_labeled.pkl"

# Winner NLL pinned here; curve lives in mechanism.fitted_control_prob.
FIT_NLL: float = 782.6

# Null (intercept-only) and assumed-curve NLL on the same 1,160 rows.
NULL_NLL: float = 793.3
ASSUMED_NLL: float = 3205.1

# Counts that pin the pool: n, controls, and completions. Complete and
# controlled are different labels: P(control | complete) = 0.596, the
# join prose mixing them must use.
POOL_N: int = 1160
POOL_CONTROLS: int = 659
POOL_COMPLETED: int = 1024
CONTROL_GIVEN_COMPLETE: float = 0.596

# Structure-delta means on the same 1,160 (all rows have +3 s windows):
# the average completed pass tightens structure — value is in the
# right tail, not the mean. Pinned to 2dp.
DELTA_PRESS_MEAN: float = -0.83
DELTA_COMPACT_MEAN: float = -0.72

# Control by pooled cushion-decile (own tenths): observed vs fitted mean.
# Monotone rising to q9, q10 dip on n=115 — noise, same tail pattern as gate 3.
DECILE_OBS = (0.431, 0.431, 0.483, 0.487, 0.578, 0.638, 0.619, 0.640, 0.707, 0.670)
DECILE_FIT = (0.318, 0.407, 0.451, 0.484, 0.515, 0.543, 0.572, 0.614, 0.664, 0.755)


def _nll(rows, fn) -> float:
    s = 0.0
    for r in rows:
        c, y = _row(r)
        p = min(max(fn(c), 1e-6), 1 - 1e-6)
        s -= y * math.log(p) + (1 - y) * math.log(1 - p)
    return s


def _row(r):
    """Pool rows are dicts with join keys; (cushion, controlled) is the fit pair."""
    if isinstance(r, dict):
        return r["cushion_s"], r["controlled"]
    return r[0], r[2]  # legacy tuple rows


def test_winner_beats_null_and_assumed():
    rows = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    assert len(rows) == POOL_N
    pairs = [_row(r) for r in rows]
    assert sum(y for _, y in pairs) == POOL_CONTROLS
    completed = [r for r in rows if r["complete"]]
    assert len(completed) == POOL_COMPLETED
    assert (
        abs(
            sum(1 for r in completed if r["controlled"]) / len(completed)
            - CONTROL_GIVEN_COMPLETE
        )
        < 0.005
    )
    null_rows = sum(y for _, y in pairs) / len(pairs)
    null = -sum(
        y * math.log(null_rows) + (1 - y) * math.log(1 - null_rows) for _, y in pairs
    )
    assert abs(null - NULL_NLL) < 1.0
    assert abs(_nll(rows, fitted_control_prob) - FIT_NLL) < 1.0
    assert abs(_nll(rows, _touch_curve_logistic_null) - ASSUMED_NLL) < 5.0
    assert FIT_NLL < NULL_NLL < ASSUMED_NLL


def test_control_by_decile_pins_curve():
    import collections

    import numpy as np

    rows = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    pairs = [_row(r) for r in rows]
    cs = sorted(c for c, _ in pairs)
    q = np.quantile(cs, [i / 10 for i in range(1, 10)])
    bins = collections.defaultdict(list)
    for c, y in pairs:
        d = sum(1 for e in q if c > e) + 1
        bins[d].append((c, y))
    assert len(bins) == 10
    for d in range(1, 11):
        obs = sum(y for _, y in bins[d]) / len(bins[d])
        pred = sum(fitted_control_prob(c) for c, _ in bins[d]) / len(bins[d])
        assert abs(obs - DECILE_OBS[d - 1]) < 0.005
        assert abs(pred - DECILE_FIT[d - 1]) < 0.005


def test_structure_delta_means_pinned():
    import numpy as np

    rows = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    assert all(isinstance(r, dict) and r["delta_press_m"] is not None for r in rows)
    press = np.array([r["delta_press_m"] for r in rows])
    comp = np.array([r["delta_compact_m"] for r in rows])
    assert abs(press.mean() - DELTA_PRESS_MEAN) < 0.02
    assert abs(comp.mean() - DELTA_COMPACT_MEAN) < 0.02


def test_q1_bias_pinned():
    import numpy as np

    rows = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    pairs = [_row(r) for r in rows]
    cs = sorted(c for c, _ in pairs)
    q = np.quantile(cs, [i / 10 for i in range(1, 10)])
    q1 = [r for r in rows if not any(r["cushion_s"] > e for e in q)]
    assert len(q1) == 116
    assert sum(1 for r in q1 if r["controlled"]) == 50
    tight = [r for r in q1 if r["marking_dist_m"] <= 2.5]
    loose = [r for r in q1 if r["marking_dist_m"] > 2.5]
    assert (sum(1 for r in tight if r["controlled"]), len(tight)) == (20, 58)
    assert (sum(1 for r in loose if r["controlled"]), len(loose)) == (30, 58)
    fitted_mean = sum(fitted_control_prob(r["cushion_s"]) for r in q1) / len(q1)
    assert abs(fitted_mean - DECILE_FIT[0]) < 0.005
    # Match-clustered bootstrap (fixed seed): q1 misfit is bias, not
    # noise — the fitted mean sits outside the 95% interval.
    by_match = {}
    for r in rows:
        by_match.setdefault(r["match"], []).append(r)
    matches = sorted(by_match)
    rng = np.random.default_rng(7)
    stats = []
    for _ in range(2000):
        samp = rng.choice(matches, size=len(matches), replace=True)
        sub = [
            r
            for m in samp
            for r in by_match[m]
            if not any(r["cushion_s"] > e for e in q)
        ]
        stats.append(sum(1 for r in sub if r["controlled"]) / len(sub))
    lo, hi = float(np.quantile(stats, 0.025)), float(np.quantile(stats, 0.975))
    assert fitted_mean < lo, (fitted_mean, lo, hi)
# Bank processing order, not calendar order (raw not vendored, dates
# unrecoverable): first 3 vs last 4 of the label script's match list.
# Levels move across splits (control 0.592 vs 0.533, hold 2.36 vs
# 1.80, dpress -1.11 vs -0.44); curve shape transfers — the first-3
# refit gains 4.9 in-sample but costs only 1.8 on held-out last-4,
# net wash. Heterogeneity is real; the functional form holds.
SPLIT_FIRST = ("J03WMX", "J03WN1", "J03WOH")

LATTICE_LAM = (0.30, 0.325, 0.35, 0.375, 0.40, 0.425, 0.45, 0.475, 0.50)
LATTICE_C0 = (
    -1.75,
    -1.70,
    -1.65,
    -1.60,
    -1.55,
    -1.50,
    -1.45,
    -1.40,
    -1.35,
    -1.30,
    -1.25,
)


def _split_nll(sub, lam, c0) -> float:
    s = 0.0
    for r in sub:
        p = 1.0 - math.exp(-lam * (r["cushion_s"] - c0)) if r["cushion_s"] > c0 else 0.0
        p = min(max(p, 1e-9), 1 - 1e-9)
        y = 1 if r["controlled"] else 0
        s -= y * math.log(p) + (1 - y) * math.log(1 - p)
    return s


def test_bank_order_split_pinned():
    import numpy as np

    rows = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    a = [r for r in rows if r["match"] in SPLIT_FIRST]
    b = [r for r in rows if r["match"] not in SPLIT_FIRST]
    assert (len(a), len(b)) == (682, 478)
    assert sum(1 for r in a if r["controlled"]) == 404
    assert sum(1 for r in b if r["controlled"]) == 255
    assert abs(float(np.median([r["hold_s"] for r in a])) - 2.36) < 0.03
    assert abs(float(np.median([r["hold_s"] for r in b])) - 1.80) < 0.03
    assert abs(float(np.mean([r["delta_press_m"] for r in a])) - (-1.11)) < 0.03
    assert abs(float(np.mean([r["delta_press_m"] for r in b])) - (-0.44)) < 0.03
    pooled_a = _split_nll(a, FIT_LAM, FIT_C0)
    pooled_b = _split_nll(b, FIT_LAM, FIT_C0)
    best = min(_split_nll(a, lam, c0) for lam in LATTICE_LAM for c0 in LATTICE_C0)
    assert abs(pooled_a - 453.7) < 1.0
    assert abs(best - 448.9) < 1.0
    assert pooled_a - best > 3.0  # refit actually moves in-sample
    refit = min(
        ((lam, c0) for lam in LATTICE_LAM for c0 in LATTICE_C0),
        key=lambda p: _split_nll(a, p[0], p[1]),
    )
    assert abs(_split_nll(b, refit[0], refit[1]) - pooled_b) < 2.0
