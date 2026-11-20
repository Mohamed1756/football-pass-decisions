"""Gate-1 hold fit: median hold + pass-within-3s by zone, exits stratified.

1,160 intervals on banked dict rows (join keys + reception position +
hold fields). Median hold 2.16 s overall (2.40 s controlled-only);
pass exits dominate (958/1160); loss is the minority exit in every
zone. Stoppage is a structural zero: the loader never emits it.
Mid releases fastest under both conditionings; controlled-only zone
order is def 2.56 / mid 2.24 / att 2.68, so att holds longest given
control.
"""

import pickle

import numpy as np

RETENTION_LABELED_PATH = "data/pooled/idsse_retention_labeled.pkl"

# Banked pool size; figures.py derives fig11's subtitle from this.
POOL_N: int = 1160

# (zone, n, median hold, pass-within-3s rate, n_pass, n_loss).
HOLD_BY_ZONE = {
    "def": (286, 2.52, 0.629, 229, 57),
    "mid": (588, 1.96, 0.703, 499, 89),
    "att": (286, 2.34, 0.596, 230, 56),
}

# Controlled-only: gate 1 conditions on control (n=659).
HOLD_BY_ZONE_CONTROLLED = {
    "def": (180, 2.56, 0.62, 150, 30),
    "mid": (316, 2.24, 0.664, 277, 39),
    "att": (163, 2.68, 0.574, 136, 27),
}


def _zone(x_m: float) -> str:
    return "def" if x_m < 35.0 else ("mid" if x_m < 70.0 else "att")


def test_hold_fit_pinned():
    rows = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    assert len(rows) == POOL_N
    assert all(r.get("hold_s") is not None for r in rows)
    for zone, (n, med, p3, npass, nloss) in HOLD_BY_ZONE.items():
        sub = [r for r in rows if _zone(r["recept_x_m"]) == zone]
        assert len(sub) == n, (zone, len(sub))
        assert abs(float(np.median([r["hold_s"] for r in sub])) - med) < 0.03
        passes = [r for r in sub if r["hold_exit"] == "pass"]
        assert len(passes) == npass
        assert len([r for r in sub if r["hold_exit"] == "loss"]) == nloss
        assert (
            abs(sum(1 for r in passes if r["hold_s"] <= 3.0) / len(passes) - p3) < 0.01
        )


def test_hold_fit_controlled_pinned():
    rows = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    assert sum(1 for r in rows if r["hold_exit"] == "stoppage") == 0
    for zone, (n, med, p3, npass, nloss) in HOLD_BY_ZONE_CONTROLLED.items():
        sub = [r for r in rows if _zone(r["recept_x_m"]) == zone and r["controlled"]]
        assert len(sub) == n, (zone, len(sub))
        assert abs(float(np.median([r["hold_s"] for r in sub])) - med) < 0.03
        passes = [r for r in sub if r["hold_exit"] == "pass"]
        assert len(passes) == npass
        assert len([r for r in sub if r["hold_exit"] == "loss"]) == nloss
        assert (
            abs(sum(1 for r in passes if r["hold_s"] <= 3.0) / len(passes) - p3) < 0.01
        )
