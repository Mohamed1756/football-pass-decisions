"""Gate-2 viability check: chosen-outlet viability conditions choice.

Pins tau = 0.0 (the physical viability line, same default as
affordance_volume's viability_thr_s) against behavior on the banked
171,440 chosen-only rows: viable-chosen passes take rank 0 at the
headline rate, non-viable-chosen passes almost never do. Chosen-only
rows cannot yield set size or entropy (unchosen margins unbanked);
this validates the threshold, not the load.
"""

import pickle

CHOICE_POOLED_PATH = "data/pooled/frozen_five_leagues.pkl"

# Per league: (viable_n, viable_rank0, nonviable_n, nonviable_rank0).
# Viable = chosen margin > 0.0. wc2022 rank-0 total = 18102 + 1,
# matching WC2022_RANK0_N in test_choice_shares.
VIABILITY_COUNTS = {
    "wc2022": (41435, 18102, 126, 1),
    "euro2020": (33661, 14854, 100, 3),
    "laliga": (28607, 11859, 87, 0),
    "euro2024": (34513, 14981, 104, 0),
    "wwc2023": (32707, 13819, 100, 1),
}


def test_choice_viability_counts_pinned():
    five = pickle.load(open(CHOICE_POOLED_PATH, "rb"))
    for league, (vn, vr, nn, nr) in VIABILITY_COUNTS.items():
        rows = five[league]
        viable = [r for r in rows if r["margin"] > 0.0]
        nonviable = [r for r in rows if not r["margin"] > 0.0]
        assert len(viable) == vn, (league, len(viable))
        assert len(nonviable) == nn, (league, len(nonviable))
        assert sum(1 for r in viable if r["rank"] == 0) == vr, league
        assert sum(1 for r in nonviable if r["rank"] == 0) == nr, league


def test_rank0_separates_on_viability():
    # Viable-chosen rank-0 share reproduces the 0.41-0.44 headline;
    # non-viable-chosen rank-0 stays under 0.05 in every league.
    five = pickle.load(open(CHOICE_POOLED_PATH, "rb"))
    for league in VIABILITY_COUNTS:
        rows = five[league]
        viable = [r for r in rows if r["margin"] > 0.0]
        nonviable = [r for r in rows if not r["margin"] > 0.0]
        pv = sum(1 for r in viable if r["rank"] == 0) / len(viable)
        pn = sum(1 for r in nonviable if r["rank"] == 0) / len(nonviable)
        assert 0.41 <= pv <= 0.45, (league, pv)
        assert pn < 0.05, (league, pn)
