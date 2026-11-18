"""Gate-0 loop test: does previous ΔS predict next openness? Null result.

1,152 linked pass pairs (same match, consecutive receptions).
corr(prev press-delta, next pre_press) ≈ +0.10 — no link. Loosening
passes are followed by marginally *more* press (6.34 vs 5.73 m) — defense
converges on the next reception regardless. The 0<->5 recurrence is
architecture, not evidence.
The 0<->5 recurrence is architecture, not evidence: defenses reset
faster than 3 s, or next openness is set by phase, not the duel.
Gate 0 measures formation independently; it does not close the loop.
"""

import pickle

import numpy as np

RETENTION_LABELED_PATH = "data/pooled/idsse_retention_labeled.pkl"

LINKED_N: int = 1152
CORR_PREV_DELTA_NEXT_OPEN: float = 0.101
OPEN_AFTER_LOOSEN: float = 6.34
OPEN_AFTER_TIGHTEN: float = 5.73


def test_loop_null_pins():
    import collections

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
            pairs.append((a["delta_press_m"], b["pre_press_m"]))
    assert len(pairs) == LINKED_N
    ds = np.array([p[0] for p in pairs])
    os_ = np.array([p[1] for p in pairs])
    assert abs(float(np.corrcoef(ds, os_)[0, 1]) - CORR_PREV_DELTA_NEXT_OPEN) < 0.02
    lo = [o for d, o in pairs if d > 0]
    hi = [o for d, o in pairs if d <= 0]
    assert abs(float(np.mean(lo)) - OPEN_AFTER_LOOSEN) < 0.05
    assert abs(float(np.mean(hi)) - OPEN_AFTER_TIGHTEN) < 0.05
