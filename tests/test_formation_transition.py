"""Gate-0 loop test: previous press-delta vs next openness.

1,152 linked pairs (same match, consecutive banked rows by pass_idx).
Unfiltered Pearson +0.10, Spearman +0.05: detected small effect (R2~=1%),
not noise at n=1,152 (MDE |r|>=0.082 at 80% power, alpha=0.05 two-sided).
The pairing is diluted: median gap 8.6 s between linked pass_idx values,
q75 40.5 s, only 39% within 5 s. Gap<=5 s subset (n=452): r=+0.25.
Previous-controlled subset (n=655, the freeze.md conditioning): r=+0.02,
null. Positive delta = structure loosened = more open, so 6.34 m after
loosening vs 5.73 m after tightening runs with persistence; the loop
hypothesis predicted the opposite sign (loosening followed by tighter
press). No usable loop signal either way; the 0<->5 recurrence stays
architecture, not evidence.
"""

import collections
import pickle
import numpy as np

RETENTION_LABELED_PATH = "data/pooled/idsse_retention_labeled.pkl"
LINKED_N: int = 1152
CORR_PREV_DELTA_NEXT_OPEN: float = 0.101
OPEN_AFTER_LOOSEN: float = 6.34
OPEN_AFTER_TIGHTEN: float = 5.73
GAP_S: float = 5.0
LINKED_N_GAP5: int = 452
CORR_GAP5: float = 0.253
LINKED_N_CONTROLLED: int = 655
CORR_CONTROLLED: float = 0.017
SPEARMAN_ALL: float = 0.046


def _linked_pairs() -> list:
    rows = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    assert all("pre_press_m" in r for r in rows)
    by_match = collections.defaultdict(list)
    for r in rows:
        if r.get("pre_press_m") is None or r.get("delta_press_m") is None:
            continue
        by_match[r["match"]].append(r)
    for m in by_match:
        by_match[m].sort(key=lambda r: r["pass_idx"])
    pairs = []
    for rs in by_match.values():
        for a, b in zip(rs, rs[1:]):
            gap_s = (b["pass_idx"] - a["pass_idx"]) / 25.0
            pairs.append(
                (a["delta_press_m"], b["pre_press_m"], gap_s, bool(a.get("controlled")))
            )
    return pairs


def _pearson(xs: list, ys: list) -> float:
    return float(np.corrcoef(np.array(xs), np.array(ys))[0, 1])


def _spearman(xs: list, ys: list) -> float:
    rx = np.argsort(np.argsort(np.array(xs))).astype(float)
    ry = np.argsort(np.argsort(np.array(ys))).astype(float)
    return float(np.corrcoef(rx, ry)[0, 1])


def test_loop_null_pins():
    pairs = _linked_pairs()
    assert len(pairs) == LINKED_N
    ds = [p[0] for p in pairs]
    os_ = [p[1] for p in pairs]
    assert abs(_pearson(ds, os_) - CORR_PREV_DELTA_NEXT_OPEN) < 0.02
    assert abs(_spearman(ds, os_) - SPEARMAN_ALL) < 0.02
    lo = [o for d, o, _, _ in pairs if d > 0]
    hi = [o for d, o, _, _ in pairs if d <= 0]
    assert abs(float(np.mean(lo)) - OPEN_AFTER_LOOSEN) < 0.05
    assert abs(float(np.mean(hi)) - OPEN_AFTER_TIGHTEN) < 0.05


def test_loop_gap5_pins():
    # Consecutive banked rows are not consecutive possession events
    # (failed receptions drop rows); gap is the start-frame delta at
    # 25 Hz, a proxy that overstates the reception gap by ball flight.
    pairs = [p for p in _linked_pairs() if p[2] <= GAP_S]
    assert len(pairs) == LINKED_N_GAP5
    assert (
        abs(_pearson([p[0] for p in pairs], [p[1] for p in pairs]) - CORR_GAP5) < 0.02
    )


def test_loop_controlled_pins():
    # freeze.md conditions the loop on control; delta conditions on the
    # previous reception, so filter on the previous row's flag.
    pairs = [p for p in _linked_pairs() if p[3]]
    assert len(pairs) == LINKED_N_CONTROLLED
    assert (
        abs(_pearson([p[0] for p in pairs], [p[1] for p in pairs]) - CORR_CONTROLLED)
        < 0.02
    )
