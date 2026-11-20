"""Pinned regression on banked evidence: literals vs pools, exact counts.

The fitted constants in calibration.py are claims about these files.
If a pool changes, this test — not a green suite — says so. Counts are
exact (failures, n), not rounded rates.
"""

import bisect
import collections
import hashlib
import json
import pickle

import numpy as np
from src.models.pressing.calibration import (
    DECILE_EDGES_S,
    DECILE_INCOMPLETION_RATE,
    RANK_INCOMPLETION_RATE,
    decile_risk,
    margin_decile,
    rank_risk,
)

EDGES = list(DECILE_EDGES_S)


def _frozen_table(rows):
    bins = collections.defaultdict(lambda: [0, 0])
    for m, inc in rows:
        d = margin_decile(m)
        bins[d][0] += inc
        bins[d][1] += 1
    return bins


def _norm(rows):
    out = []
    for r in rows:
        if isinstance(r, dict):
            out.append((r["margin"], 0 if r["complete"] else 1))
        else:
            out.append((r[0], r[1]))
    return out


def test_wc2022_edges_reproduce_pinned_rates():
    five = pickle.load(open("data/pooled/frozen_five_leagues.pkl", "rb"))
    bins = _frozen_table(_norm(five["wc2022"]))
    # exact pinned counts: d1 856/4188, d10 9/4114
    assert (bins[1][0], bins[1][1]) == (856, 4188)
    assert (bins[10][0], bins[10][1]) == (9, 4114)
    # literals track the pool within 3e-3 (d2/d3 fit-set rounding differs:
    # pool d2 0.130/d3 0.087 vs literals 0.131/0.085 — the fit ran on a
    # cut the banked pool does not reproduce exactly; shape holds).
    for d in range(1, 11):
        got = bins[d][0] / bins[d][1]
        assert abs(got - DECILE_INCOMPLETION_RATE[d - 1]) < 3e-3
        assert abs(got - decile_risk(d)) < 3e-3


def test_rank_literals_reproduce_wc2022_curve():
    five = pickle.load(open("data/pooled/frozen_five_leagues.pkl", "rb"))
    by_rank = collections.defaultdict(lambda: [0, 0])
    for r in five["wc2022"]:
        d = min(r["rank"], 7)
        by_rank[d][0] += 0 if r["complete"] else 1
        by_rank[d][1] += 1
    for d in range(8):
        got = by_rank[d][0] / by_rank[d][1]
        assert abs(got - RANK_INCOMPLETION_RATE[d]) < 5e-4
        assert abs(got - rank_risk(d)) < 5e-4


def test_canonical_targeted_pool_shape():
    frozen, live = pickle.load(
        open("data/pooled/skillcorner_targeted_frozen_live.pkl", "rb")
    )
    assert len(frozen) == len(live) == 14822
    bins = _frozen_table(frozen)
    # frozen-edge d1 on canonical pool: 1948/8645
    assert (bins[1][0], bins[1][1]) == (1948, 8645)
    # base incompletion both margins: 2337/14822 = 0.1577 ("16%")
    assert sum(inc for _, inc in frozen) == 2337
    assert sum(inc for _, inc in live) == 2337


LEAGUES = ("wc2022", "euro2020", "laliga", "euro2024", "wwc2023")

# Leave-one-league-out: edges refit as deciles of the other four
# leagues' margins, held-out league binned on them. Exact (fail, n)
# for the endpoint deciles; the gradient is shape, not edges.
LOLO_ENDPOINTS = {
    "wc2022": ((764, 3753), (18, 5322)),
    "euro2020": ((722, 3556), (13, 3302)),
    "laliga": ((656, 3255), (4, 1844)),
    "euro2024": ((600, 2770), (5, 3180)),
    "wwc2023": ((1053, 3818), (18, 3668)),
}


def test_lolo_deciles_survive():
    five = pickle.load(open("data/pooled/frozen_five_leagues.pkl", "rb"))
    d1 = {}
    for held in LEAGUES:
        train = [r["margin"] for lg in LEAGUES if lg != held for r in five[lg]]
        edges = [
            float(np.quantile(train, q))
            for q in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
        ]
        bins = collections.defaultdict(lambda: [0, 0])
        for r in five[held]:
            # Left-closed, like margin_decile (m <= edge falls lower):
            # one binning rule for the whole project.
            d = bisect.bisect_left(edges, r["margin"]) + 1
            inc = 0 if r["complete"] else 1
            bins[d][0] += inc
            bins[d][1] += 1
        rates = [bins[d][0] / bins[d][1] for d in range(1, 11)]
        assert all(rates[i] > rates[i + 1] for i in range(9)), (held, rates)
        (f1, n1), (f10, n10) = LOLO_ENDPOINTS[held]
        assert (bins[1][0], bins[1][1]) == (f1, n1), (held, bins[1])
        assert (bins[10][0], bins[10][1]) == (f10, n10), (held, bins[10])
        assert bins[10][0] / bins[10][1] <= 0.005, (held, rates[9])
        d1[held] = rates[0]
    for held in ("wc2022", "euro2020", "laliga", "euro2024"):
        assert 0.19 <= d1[held] <= 0.23, (held, d1[held])
    assert 0.26 <= d1["wwc2023"] <= 0.29, d1


# Per-team ns from the match_teams.json join (reproduce.py logic).
# fig3/table plot 13,122 labeled passes; the pool banks 14,822 live
# rows, all with int outcomes — the 1,700-row plot filter is unbanked,
# so the banked side is pinned here and the plot n must be recounted,
# never assumed, downstream.
TEAM_NS = {
    "Adelaide United": 1259,
    "Auckland FC": 2450,
    "Brisbane FC": 1187,
    "CC Mariners": 1227,
    "Macarthur FC": 617,
    "Melbourne City": 1541,
    "Melbourne V FC": 1544,
    "Newcastle": 364,
    "Perth Glory": 662,
    "Sydney FC": 798,
    "Wellington P FC": 1018,
    "Western Sydney": 814,
    "Western United": 1341,
}


def test_team_join_recovers_banked_counts():
    fp = pickle.load(open("data/pooled/skillcorner_team_margins.pkl", "rb"))
    assert len(fp) == 40
    assert sum(len(v) for v in fp.values()) == 14822
    meta = json.load(open("data/pooled/match_teams.json"))
    assert len(meta) == 20
    teams = collections.defaultdict(list)
    skipped = 0
    for (mid, side), rows in fp.items():
        if mid not in meta:
            skipped += len(rows)
            continue
        teams[meta[mid][side]].extend(rows)
    assert skipped == 0
    assert sum(len(v) for v in teams.values()) == 14822
    assert set(teams) == set(TEAM_NS)
    for t, n in TEAM_NS.items():
        assert len(teams[t]) == n, (t, len(teams[t]))
    assert all(
        isinstance(r, (list, tuple)) and r[1] is not None
        for v in fp.values()
        for r in v
    )


# sha256 of every banked pool with no generator. Content tests pin
# counts and rates; these pins catch byte-level drift they cannot —
# row reorderings, sub-bin edits, float churn. Any byte change to a
# generator-less frozen input is unaccounted drift, so reorderings
# fail here by design. idsse_retention_labeled.pkl is excluded: it
# has a generator (label_retention.py) and deep content pins, and a
# byte pin would false-fail a legitimate re-bank.
POOL_SHA256 = {
    "frozen_five_leagues.pkl": "314233b3ee420e8eede32e3f36e8265266ad0d4695d7efe685266436b882dc12",
    "idsse_ball_flights.pkl": "b54c254ad06f29290d31ccc92e482ea2a93a456af131dddf4be94d09de6e8194",
    "idsse_measured_all_1160.pkl": "16449cd8744d791c3592e3082e9615c7a1b1580bc0882e3705b0a72d1c13c23a",
    "idsse_measured_live.pkl": "1a14700e183fa85926f2eab8d4daa5d540e4d7d59cdc74d58a805baa94836dd2",
    "idsse_pooled7.pkl": "177464fb03b3de248d7c475ce6f4edca840cc0f889c96bd65848686b075aa642",
    "idsse_reception_speeds.pkl": "add724dd927a592f441e0ae125d433b67cca8c88c46d45ee8bf0cca4699df903",
    "idsse_rematch_656.pkl": "7631c5fc7223e74b5a443ae1c4cfbd9764ed6c0378a93835666f41e9f958656c",
    "skillcorner_frozen_live.pkl": "357f2e18a09bc1d889b527f2c49e35c2e25a686ca3c346cadfb793a983aa6222",
    "skillcorner_targeted_frozen_live.pkl": "81f0d76e97df5aa672aee2c4044689b5a293b15a036b55611b1a79b2f3b22b45",
    "skillcorner_team_margins.pkl": "b01df8c2ee08fe0d5b5c0dcd3e91e45fd502fe59ea921e5b282f8b69b778ce23",
    "value_choice_by_passer.pkl": "1c16059f00bdc161ac7e2f0a42e52ff94e6dbbb42c06bad77ab8233428b0db89",
}


def test_pool_bytes_pinned():
    for name, want in POOL_SHA256.items():
        h = hashlib.sha256()
        with open(f"data/pooled/{name}", "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        assert h.hexdigest() == want, name


# Exactly one incomplete row (J03WN1/100082, missing -5 s tracks):
# pre_press_m and pre_sep_vel are each None once, on that row; every
# other field is present on all 1,160 rows. Column growth that drops
# coverage anywhere fails here with the field named.
NONE_COUNTS = {"pre_press_m": 1, "pre_sep_vel": 1}


def test_pool_none_profile_pinned():
    rows = pickle.load(open("data/pooled/idsse_retention_labeled.pkl", "rb"))
    assert len(rows) == 1160
    keys = set()
    for r in rows:
        keys.update(r.keys())
    for k in sorted(keys):
        n = sum(1 for r in rows if r.get(k) is None)
        assert n == NONE_COUNTS.get(k, 0), (k, n)
    bad = [r for r in rows if r.get("pre_press_m") is None]
    assert [(r["match"], r["pass_idx"]) for r in bad] == [("J03WN1", 100082)]
    assert all(r.get("pre_sep_vel") is None for r in bad)
    have = [r for r in rows if r.get("pre_press_m") is not None]
    assert len(have) == 1159


# IDSSE measured pool on frozen WC2022 edges (the table reproduce.py
# prints; no other test pins it). Noisy tail past d4 — counts are the
# contract, not shape.
IDSSE_FROZEN_EDGE_COUNTS = (
    (92, 532),
    (26, 222),
    (9, 93),
    (3, 74),
    (3, 55),
    (1, 32),
    (1, 21),
    (0, 33),
    (0, 26),
    (1, 72),
)


def test_idsse_frozen_edge_table_pinned():
    both = pickle.load(open("data/pooled/idsse_measured_all_1160.pkl", "rb"))
    assert len(both) == 1160
    bins = collections.defaultdict(lambda: [0, 0])
    for m, inc in both:
        d = margin_decile(m)
        bins[d][0] += inc
        bins[d][1] += 1
    for d in range(1, 11):
        assert (bins[d][0], bins[d][1]) == IDSSE_FROZEN_EDGE_COUNTS[d - 1], d
