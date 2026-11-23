"""Gate-0/2 choice sets: per-freeze viable size + entropy vs chosen rank.

Banked by scripts/label_choice_sets.py from the 7 raw IDSSE matches
(HuggingFace pysport/idsse-data): one row per pass with an observed
reception (same conditioning as the retention pool, hence the same
n=1,160). Frozen margins match the calibration convention. The load
test: rank-0 share falls as viable-set size and effective options
rise, monotone across every bin.
"""

import collections
import pickle

import numpy as np

CHOICE_SETS_PATH = "data/pooled/idsse_choice_sets_labeled.pkl"
RETENTION_LABELED_PATH = "data/pooled/idsse_retention_labeled.pkl"

PER_MATCH_N = {
    "J03WMX": 312,
    "J03WN1": 285,
    "J03WOH": 85,
    "J03WOY": 82,
    "J03WQQ": 109,
    "J03WR9": 130,
    "J03WPY": 157,
}

# Passer-exclusion fallbacks per match (name lookup missed the pitch;
# nearest non-target mate excluded instead, target never taken).
FALLBACK_N = {
    "J03WMX": 35,
    "J03WN1": 29,
    "J03WOH": 5,
    "J03WOY": 10,
    "J03WQQ": 25,
    "J03WR9": 12,
    "J03WPY": 20,
}

# Exact chosen-rank histogram (rank 7 pools 7+).
RANK_HIST = {0: 251, 1: 421, 2: 193, 3: 117, 4: 71, 5: 50, 6: 28, 7: 29}

# (n, rank-0 n) per load bin: strictly falling shares both ways.
NV_BINS = {"<=7": (240, 128), "8": (238, 44), "9": (304, 49), ">=10": (378, 30)}
EF_BINS = {
    "<=5": (103, 67),
    "(5,7]": (407, 112),
    "(7,9]": (541, 62),
    ">9": (109, 10),
}

# (zone, n, mean n_viable, mean effective_options). Joined to the
# retention pool on (match, pass_idx, target_id) for recept_x_m; full
# 1,160 cover, so mid carries one more row than the formation table
# (whose −5 s window drops one track).
ZONE_MEANS = {
    "def": (286, 8.33, 6.89),
    "mid": (588, 8.99, 7.49),
    "att": (286, 7.93, 6.58),
}


def _zone(x_m: float) -> str:
    return "def" if x_m < 35.0 else ("mid" if x_m < 70.0 else "att")


def test_choice_sets_pool_pinned():
    rows = pickle.load(open(CHOICE_SETS_PATH, "rb"))
    assert len(rows) == 1160
    assert dict(collections.Counter(r["match"] for r in rows)) == PER_MATCH_N
    fb = collections.Counter(r["match"] for r in rows if r.get("passer_fallback"))
    assert dict(sorted(fb.items())) == FALLBACK_N
    hist = collections.Counter(min(r["chosen_rank"], 7) for r in rows)
    assert dict(sorted(hist.items())) == RANK_HIST


def _bin(rows, key, pred):
    sub = [r for r in rows if pred(r[key])]
    return len(sub), sum(1 for r in sub if r["chosen_rank"] == 0)


def test_load_gradient_pinned():
    rows = pickle.load(open(CHOICE_SETS_PATH, "rb"))
    nv = {
        "<=7": lambda v: v <= 7,
        "8": lambda v: v == 8,
        "9": lambda v: v == 9,
        ">=10": lambda v: v >= 10,
    }
    ef = {
        "<=5": lambda v: v <= 5,
        "(5,7]": lambda v: 5 < v <= 7,
        "(7,9]": lambda v: 7 < v <= 9,
        ">9": lambda v: v > 9,
    }
    nv_shares = []
    for name, pred in nv.items():
        assert _bin(rows, "n_viable", pred) == NV_BINS[name], name
        n, r0 = NV_BINS[name]
        nv_shares.append(r0 / n)
    assert all(a > b for a, b in zip(nv_shares, nv_shares[1:])), nv_shares
    ef_shares = []
    for name, pred in ef.items():
        assert _bin(rows, "effective_options", pred) == EF_BINS[name], name
        n, r0 = EF_BINS[name]
        ef_shares.append(r0 / n)
    assert all(a > b for a, b in zip(ef_shares, ef_shares[1:])), ef_shares


def test_choice_sets_zone_means():
    rows = pickle.load(open(CHOICE_SETS_PATH, "rb"))
    ret = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    rx = {(r["match"], r["pass_idx"], r["target_id"]): r["recept_x_m"] for r in ret}
    assert len(rx) == 1160
    for zone, (n, nv, eff) in ZONE_MEANS.items():
        sub = [
            r
            for r in rows
            if _zone(rx[(r["match"], r["pass_idx"], r["target_id"])]) == zone
        ]
        assert len(sub) == n, (zone, len(sub))
        assert abs(float(np.mean([r["n_viable"] for r in sub])) - nv) < 0.03
        assert abs(float(np.mean([r["effective_options"] for r in sub])) - eff) < 0.03
