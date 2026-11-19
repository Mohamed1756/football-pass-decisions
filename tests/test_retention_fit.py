"""Pinned retention fit: first contest on banked labels, exact counts.

Gate 4 slice 3 result. The assumed logistic (k=15, mid=0.15) is not a
fit — it loses to the null by 2412 NLL. The winner is a shifted
exponential in cushion; marking adds a small residual gain.
Winner params live in mechanism (single home); this file pins NLLs.
"""

import math
import pickle

from src.models.retention.mechanism import fitted_control_prob


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

# Counts that pin the pool: n and controls.
POOL_N: int = 1160
POOL_CONTROLS: int = 659

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
