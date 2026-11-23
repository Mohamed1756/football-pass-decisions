"""Load-vs-hold null: choice load carries no hold-timing signal.

Joins the banked choice sets to hold_s on (match, pass_idx, target_id)
(full 1,160 cover). Load predicts choice quality (rank-0 0.53 -> 0.08
in test_choice_sets_table) but not duration: |corr| < 0.10 on both
binnings, bin medians flat. Bounds affordance volume to gate 2 and
keeps gate 1's shape null intact.
"""

import pickle

import numpy as np

CHOICE_SETS_PATH = "data/pooled/idsse_choice_sets_labeled.pkl"
RETENTION_LABELED_PATH = "data/pooled/idsse_retention_labeled.pkl"

# Median hold_s per viable-size bin: all receptions, then controlled-only.
HOLD_BY_NV = {
    "<=7": (2.40, 2.44),
    "8": (2.36, 2.52),
    "9": (2.04, 2.44),
    ">=10": (2.04, 2.16),
}


def _joined():
    sets = pickle.load(open(CHOICE_SETS_PATH, "rb"))
    ret = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    rx = {(r["match"], r["pass_idx"], r["target_id"]): r for r in ret}
    assert len(rx) == 1160
    pairs = [(s, rx[(s["match"], s["pass_idx"], s["target_id"])]) for s in sets]
    assert len(pairs) == 1160
    return pairs


def test_load_hold_null():
    pairs = _joined()
    nv = np.array([s["n_viable"] for s, _ in pairs])
    ef = np.array([s["effective_options"] for s, _ in pairs])
    hold = np.array([r["hold_s"] for _, r in pairs])
    assert abs(float(np.corrcoef(nv, hold)[0, 1])) < 0.10
    assert abs(float(np.corrcoef(ef, hold)[0, 1])) < 0.10
    bins = {
        "<=7": lambda v: v <= 7,
        "8": lambda v: v == 8,
        "9": lambda v: v == 9,
        ">=10": lambda v: v >= 10,
    }
    for name, pred in bins.items():
        sub = [(s, r) for s, r in pairs if pred(s["n_viable"])]
        med_all, med_ctl = HOLD_BY_NV[name]
        assert abs(float(np.median([r["hold_s"] for _, r in sub])) - med_all) < 0.05
        ctl = [r for _, r in sub if r["controlled"]]
        assert abs(float(np.median([r["hold_s"] for r in ctl])) - med_ctl) < 0.05
