"""Structure-delta zone table: E[dS | controlled, reception zone].

Gate 5 slice 3 result. Means on the banked 1,160 dict rows (join keys
+ reception position + 3 deltas). Controlled receptions tighten
structure everywhere (press and compactness go negative); failed
controls loosen mid (press +0.44) — the ball is already moving the
other way.
"""

import pickle

import numpy as np

RETENTION_LABELED_PATH = "data/pooled/idsse_retention_labeled.pkl"

# (zone, controlled) -> (n, mean press, mean open, mean compact), 2dp.
ZONE_MEANS = {
    ("def", True): (180, -1.40, 0.09, -2.31),
    ("def", False): (106, -0.03, 0.15, 0.41),
    ("mid", True): (316, -1.08, 0.17, -0.22),
    ("mid", False): (272, 0.44, 0.21, 0.59),
    ("att", True): (163, -2.52, 0.01, -2.19),
    ("att", False): (123, -0.67, 0.04, -1.56),
}


def _zone(x_m: float) -> str:
    return "def" if x_m < 35.0 else ("mid" if x_m < 70.0 else "att")


def test_zone_means_pinned():
    rows = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    assert len(rows) == 1160
    assert all(isinstance(r, dict) and "recept_x_m" in r for r in rows)
    for (zone, ctl), (n, press, om, comp) in ZONE_MEANS.items():
        sub = [
            r for r in rows if _zone(r["recept_x_m"]) == zone and r["controlled"] == ctl
        ]
        assert len(sub) == n, (zone, ctl, len(sub))
        assert abs(np.mean([r["delta_press_m"] for r in sub]) - press) < 0.03
        assert abs(np.mean([r["delta_open_men"] for r in sub]) - om) < 0.03
        assert abs(np.mean([r["delta_compact_m"] for r in sub]) - comp) < 0.03
