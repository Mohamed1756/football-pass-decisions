"""Gate-0 formation table + loop null: what freezes look like, by zone."""

import pickle

import numpy as np

RETENTION_LABELED_PATH = "data/pooled/idsse_retention_labeled.pkl"

# (zone, n, mean pre_press, mean pre_sep_vel).
FORMATION_BY_ZONE = {
    "def": (286, 5.52, -0.329),
    "mid": (587, 5.57, -0.280),
    "att": (286, 7.18, -0.293),
}


def _zone(x_m: float) -> str:
    return "def" if x_m < 35.0 else ("mid" if x_m < 70.0 else "att")


def test_formation_table_pinned():
    rows = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    have = [r for r in rows if r.get("pre_press_m") is not None]
    assert len(have) == 1159
    for zone, (n, press, sep) in FORMATION_BY_ZONE.items():
        sub = [r for r in have if _zone(r["recept_x_m"]) == zone]
        assert len(sub) == n, (zone, len(sub))
        assert abs(float(np.mean([r["pre_press_m"] for r in sub])) - press) < 0.03
        assert abs(float(np.mean([r["pre_sep_vel"] for r in sub])) - sep) < 0.005
