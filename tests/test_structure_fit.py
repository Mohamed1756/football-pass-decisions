"""Structure-delta zone table: shape 3 s after receipt, by zone x control.

Gate 5 slice 3 result. Means on the banked 1,160 dict rows (join keys
+ reception position + 2 deltas). Controlled receptions read tighter on
average everywhere; failed mid reads +0.44 press against a -0.08 median.
Value lives in the right tail on both sides: a quarter to a third of
controlled receptions loosen press access. Open-man column cut with the
mechanism (noise with a name).
"""

import pickle

import numpy as np

RETENTION_LABELED_PATH = "data/pooled/idsse_retention_labeled.pkl"

# (zone, controlled) -> (n, mean press, mean compact), 2dp.
ZONE_MEANS = {
    ("def", True): (180, -1.40, -2.31),
    ("def", False): (106, -0.03, 0.41),
    ("mid", True): (316, -1.08, -0.22),
    ("mid", False): (272, 0.44, 0.59),
    ("att", True): (163, -2.52, -2.19),
    ("att", False): (123, -0.67, -1.56),
}


def _zone(x_m: float) -> str:
    return "def" if x_m < 35.0 else ("mid" if x_m < 70.0 else "att")


def test_zone_means_pinned():
    rows = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    assert len(rows) == 1160
    assert all(isinstance(r, dict) and "recept_x_m" in r for r in rows)
    for (zone, ctl), (n, press, comp) in ZONE_MEANS.items():
        sub = [
            r for r in rows if _zone(r["recept_x_m"]) == zone and r["controlled"] == ctl
        ]
        assert len(sub) == n, (zone, ctl, len(sub))
        assert abs(np.mean([r["delta_press_m"] for r in sub]) - press) < 0.03
        assert abs(np.mean([r["delta_compact_m"] for r in sub]) - comp) < 0.03


# (zone, controlled) -> (n, P(delta_press>0), P(delta_press>2), q90), rates ±0.01.
RIGHT_TAIL = {
    ("def", True): (180, 0.356, 0.161, 2.96),
    ("def", False): (106, 0.481, 0.264, 5.96),
    ("mid", True): (316, 0.351, 0.212, 4.53),
    ("mid", False): (272, 0.478, 0.320, 5.43),
    ("att", True): (163, 0.258, 0.117, 2.24),
    ("att", False): (123, 0.398, 0.252, 5.23),
}


def test_right_tail_pinned():
    rows = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    for (zone, ctl), (n, p0, p2, q90) in RIGHT_TAIL.items():
        sub = [
            r["delta_press_m"]
            for r in rows
            if _zone(r["recept_x_m"]) == zone and r["controlled"] == ctl
        ]
        assert len(sub) == n, (zone, ctl, len(sub))
        assert abs(sum(1 for v in sub if v > 0) / n - p0) < 0.01
        assert abs(sum(1 for v in sub if v > 2) / n - p2) < 0.01
        assert abs(float(np.quantile(sub, 0.9)) - q90) < 0.03


def test_window_contamination_pinned():
    # 65% of rows have their next event inside the +3 s window: the
    # delta reads shape after the next action started, not what the
    # pass did. Split mean documents the artifact direction.
    rows = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    early = [r["delta_press_m"] for r in rows if r["hold_s"] < 3.0]
    late = [r["delta_press_m"] for r in rows if r["hold_s"] >= 3.0]
    assert abs(len(early) / len(rows) - 0.65) < 0.01
    assert abs(float(np.mean(early)) - (-0.71)) < 0.03
    assert abs(float(np.mean(late)) - (-1.06)) < 0.03
