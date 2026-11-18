"""Gate 0->1 composition null: pre-freeze shape carries no hold signal."""

import pickle

import numpy as np

RETENTION_LABELED_PATH = "data/pooled/idsse_retention_labeled.pkl"


def test_hold_freeze_null():
    rows = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    have = [
        r
        for r in rows
        if r.get("pre_press_m") is not None and r.get("hold_s") is not None
    ]
    assert len(have) == 1159
    for var in ("pre_press_m", "pre_sep_vel"):
        x = np.array([r[var] for r in have])
        y = np.array([r["hold_s"] for r in have])
        assert abs(float(np.corrcoef(x, y)[0, 1])) < 0.10, var
    med = float(np.median([r["hold_s"] for r in have]))
    lo = [r["hold_s"] for r in have if r["pre_sep_vel"] <= 0]
    hi = [r["hold_s"] for r in have if r["pre_sep_vel"] > 0]
    assert abs(float(np.median(lo)) - 2.26) < 0.05
    assert abs(float(np.median(hi)) - 2.0) < 0.05
    assert med > 0
