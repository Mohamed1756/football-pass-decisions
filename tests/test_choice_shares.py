"""Gate-2 choice shares: P(choose rank r), pooled, by league.

No loader changes, no raw needed — counts the banked 171,440
one-row-per-pass dicts. The rank-0 headline becomes a pinned table.
Zone/spread splits wait for a re-bank with pass grouping.
"""

import collections
import pickle

CHOICE_POOLED_PATH = "data/pooled/frozen_five_leagues.pkl"

# Total banked choice rows; figures.py derives fig12's subtitle from this.
CHOICE_TOTAL: int = 171440

# WC2022 rank-0 choice: 18,103 of 41,561.
WC2022_N: int = 41561
WC2022_RANK0_N: int = 18103

# Choice shares by rank (0-6, 7+ pooled) per league, 4dp.
CHOICE_SHARES = {
    "wc2022": (0.4356, 0.2516, 0.1434, 0.0823, 0.0458, 0.0243, 0.0108, 0.0063),
    "euro2020": (0.4401, 0.2452, 0.1381, 0.085, 0.0475, 0.0251, 0.0123, 0.0069),
    "laliga": (0.4133, 0.2409, 0.1419, 0.0897, 0.0542, 0.0338, 0.0165, 0.0097),
    "euro2024": (0.4328, 0.2502, 0.1439, 0.0806, 0.0478, 0.0241, 0.0132, 0.0075),
    "wwc2023": (0.4213, 0.2501, 0.147, 0.091, 0.0485, 0.0249, 0.0116, 0.0056),
}


def test_choice_shares_pinned():
    five = pickle.load(open(CHOICE_POOLED_PATH, "rb"))
    assert sum(len(v) for v in five.values()) == CHOICE_TOTAL
    wc = five["wc2022"]
    assert len(wc) == WC2022_N
    assert sum(1 for r in wc if r["rank"] == 0) == WC2022_RANK0_N
    for league, shares in CHOICE_SHARES.items():
        by = collections.Counter(min(r["rank"], 7) for r in five[league])
        tot = len(five[league])
        for d in range(8):
            assert abs(by[d] / tot - shares[d]) < 5e-4, (league, d)


def test_choice_top2_robust_to_tail():
    # Rank 7+ is the only bin with n<300 per league (184-277 rows).
    # Dropping it and renormalizing moves top-2 by +0.004 to +0.006,
    # pooled and per league: the tail does not wag the headline.
    five = pickle.load(open(CHOICE_POOLED_PATH, "rb"))
    for league in CHOICE_SHARES:
        rows = five[league]
        full = sum(1 for r in rows if r["rank"] <= 1) / len(rows)
        kept = [r for r in rows if r["rank"] <= 6]
        assert len(rows) - len(kept) < 300
        renorm = sum(1 for r in kept if r["rank"] <= 1) / len(kept)
        assert 0.0 <= renorm - full < 0.007, (league, full, renorm)
