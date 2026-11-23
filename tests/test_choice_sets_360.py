"""LaLiga 360 choice sets: set-size-conditioned choice + value identity.

Banked by scripts/label_360_choice_sets.py from 35 open-data matches
(StatsBomb 360 freeze frames, in-frame teammates only). The pool this
project's choice gate could never condition on: full in-frame sets with
frozen margins, so the mechanical small-set mass is measured, not
bounded. Nearest-to-end recipient mapping; verification distance banked
per row (verify_ok rate pinned, not used as a filter).
"""

import pickle

POOL_PATH = "data/pooled/sb360_laliga_choice_sets.pkl"


def test_360_pool_pinned():
    rows = pickle.load(open(POOL_PATH, "rb"))
    assert len(rows) == 26906
    assert len({r["match"] for r in rows}) == 35
    assert sum(1 for r in rows if r["chosen_rank"] == 0) == 11602
    assert sum(1 for r in rows if r["chosen_rank"] <= 1) == 18129
    assert sum(1 for r in rows if r["verify_ok"]) == 17320


def test_360_load_gradient_pinned():
    rows = pickle.load(open(POOL_PATH, "rb"))
    bins = {"<=7": (0, 7), "8": (8, 8), "9": (9, 9), ">=10": (10, 99)}
    expect = {
        "<=7": (17630, 8332),
        "8": (5383, 2009),
        "9": (3683, 1231),
        ">=10": (210, 30),
    }
    shares = []
    for name, (lo, hi) in bins.items():
        sub = [r for r in rows if lo <= r["n_viable"] <= hi]
        assert (len(sub), sum(1 for r in sub if r["chosen_rank"] == 0)) == expect[name]
        shares.append(expect[name][1] / expect[name][0])
    assert all(a > b for a, b in zip(shares, shares[1:])), shares


def test_360_set_size_top2_pinned():
    rows = pickle.load(open(POOL_PATH, "rb"))
    assert (
        abs(sum(1 for r in rows if r["chosen_rank"] <= 1) / len(rows) - 0.6738) < 1e-4
    )
    big = [r for r in rows if r["n_outlets"] >= 3]
    assert len(big) == 26801
    assert abs(sum(1 for r in big if r["chosen_rank"] <= 1) / len(big) - 0.6725) < 1e-4


def test_360_value_identity_pinned():
    rows = pickle.load(open(POOL_PATH, "rb"))
    have = [r for r in rows if any(v is not None for v in r["values"])]
    assert len(have) == 16355

    def rank0(vals):
        return sorted(range(len(vals)), key=lambda i: vals[i], reverse=True)[0]

    nv = sum(
        1
        for r in have
        if r["chosen_idx"] == rank0([v if v is not None else -1 for v in r["values"]])
    )
    nm = sum(1 for r in have if r["chosen_rank"] == 0)
    assert nv == 5824
    assert nm == 7022
