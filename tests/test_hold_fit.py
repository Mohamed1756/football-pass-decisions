"""Gate-1 hold fit: median hold + pass-within-3s by zone, exits stratified.

1,160 intervals on banked dict rows (join keys + reception position +
hold fields). Median hold 2.16 s overall; pass exits dominate
(958/1160); loss is the minority exit in every zone.
"""

import pickle

import numpy as np

RETENTION_LABELED_PATH = "data/pooled/idsse_retention_labeled.pkl"

# (zone, n, median hold, pass-within-3s rate, n_pass, n_loss).
HOLD_BY_ZONE = {
    "def": (286, 2.52, 0.629, 229, 57),
    "mid": (588, 1.96, 0.703, 499, 89),
    "att": (286, 2.34, 0.596, 230, 56),
}


def _zone(x_m: float) -> str:
    return "def" if x_m < 35.0 else ("mid" if x_m < 70.0 else "att")


def test_hold_fit_pinned():
    rows = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    assert len(rows) == 1160
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
