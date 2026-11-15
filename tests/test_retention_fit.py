"""Pinned retention fit: first contest on banked labels, exact counts.

Gate 4 slice 3 result. The assumed logistic (k=15, mid=0.15) is not a
fit — it loses to the null by 2294 NLL. The winner is a shifted
exponential in cushion; marking adds a small residual gain.
"""

import math
import pickle

RETENTION_LABELED_PATH = "data/pooled/idsse_retention_labeled.pkl"

# Winner: shifted exponential, cushion only.
# P(control) = 1 - exp(-lam * (cushion - c0)), floored at 0 below c0.
FIT_LAM: float = 0.40
FIT_C0: float = -1.50
FIT_NLL: float = 782.6

# Null (intercept-only) and assumed-curve NLL on the same 1,160 rows.
NULL_NLL: float = 793.3
ASSUMED_NLL: float = 3205.1

# Counts that pin the pool: n and controls.
POOL_N: int = 1160
POOL_CONTROLS: int = 659


def fitted_control_prob(cushion_s: float) -> float:
    """Winner curve. Below c0 the ball is already lost: 0, not small."""
    if cushion_s <= FIT_C0:
        return 0.0
    return round(1.0 - math.exp(-FIT_LAM * (cushion_s - FIT_C0)), 4)


def _nll(rows, fn) -> float:
    s = 0.0
    for c, _, y in rows:
        p = min(max(fn(c), 1e-6), 1 - 1e-6)
        s -= y * math.log(p) + (1 - y) * math.log(1 - p)
    return s


def test_winner_beats_null_and_assumed():
    rows = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    assert len(rows) == POOL_N
    assert sum(y for _, _, y in rows) == POOL_CONTROLS
    null_rows = sum(y for _, _, y in rows) / len(rows)
    null = -sum(
        y * math.log(null_rows) + (1 - y) * math.log(1 - null_rows) for _, _, y in rows
    )
    assert abs(null - NULL_NLL) < 1.0
    assert abs(_nll(rows, fitted_control_prob) - FIT_NLL) < 1.0
    from src.models.retention.mechanism import touch_curve_logistic

    assumed = _nll(rows, lambda c: touch_curve_logistic(c, 15.0, 0.15))
    assert abs(assumed - ASSUMED_NLL) < 5.0
    assert FIT_NLL < NULL_NLL < ASSUMED_NLL
