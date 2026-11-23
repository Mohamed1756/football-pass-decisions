"""Diagnostic: delta_press on receipt-level before + in-window indicator.

Loads raw IDSSE frames (same /tmp/idsse_raw prerequisite as the label
scripts), recomputes the reception frame per banked row with
_reception_point, and scores receipt-frame press access
(nearest-opponent distance to ball, _nearest_opp_dist definition).
Quantile regression (median + q90, asymmetric IRLS) of delta on
receipt-before + I(hold<3s), per zone x control cell plus pooled.
Read-only on the banked pool; raw read, nothing banked.
"""

import math
import pickle
import sys

sys.path.insert(0, ".")

from src.io.idsse import (
    _load_roster,
    _read_tracking,
    _reception_point,
)

POOL_PATH = "data/pooled/idsse_retention_labeled.pkl"
MATCHES = ["J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WQQ", "J03WR9", "J03WPY"]


def _nearest(xs, ball):
    return min(math.dist(ball, o) for o in xs) if xs else math.inf


def _qfit(X, y, tau, iters=200):
    b = [0.0, -1.0, 0.0]
    n = len(y)
    for _ in range(iters):
        A = [[0.0] * 4 for _ in range(3)]
        for i in range(n):
            r = y[i] - sum(X[i][j] * b[j] for j in range(3))
            w = (tau if r >= 0 else (1.0 - tau)) / max(abs(r), 1e-6)
            for a in range(3):
                for c in range(3):
                    A[a][c] += w * X[i][a] * X[i][c]
                A[a][3] += w * X[i][a] * y[i]
        ok = True
        for col in range(3):
            piv = max(range(col, 3), key=lambda q: abs(A[q][col]))
            A[col], A[piv] = A[piv], A[col]
            if abs(A[col][col]) < 1e-12:
                ok = False
                break
            for q in range(3):
                if q != col:
                    f = A[q][col] / A[col][col]
                    for c in range(col, 4):
                        A[q][c] -= f * A[col][c]
        if not ok:
            break
        nb = [A[a][3] / A[a][a] if abs(A[a][a]) > 1e-12 else b[a] for a in range(3)]
        if max(abs(x - y_) for x, y_ in zip(nb, b)) < 1e-9:
            b = nb
            break
        b = nb
    return b


def main() -> None:
    rows = pickle.load(open(POOL_PATH, "rb"))
    have = [r for r in rows if r.get("pre_press_m") is not None]
    by_match = {}
    for r in have:
        by_match.setdefault(r["match"], []).append(r)

    scored = []
    missing = 0
    for m in MATCHES:
        c = "000001" if m in ("J03WMX", "J03WN1") else "000002"
        base = "/tmp/idsse_raw/DFL"
        mp = f"{base}_02_01_matchinformation_DFL-COM-{c}_DFL-MAT-{m}.xml"
        pp = f"{base}_04_03_positions_raw_observed_DFL-COM-{c}_DFL-MAT-{m}.xml"
        length, width, teams, names = _load_roster(mp)
        frames, ball, stamps = _read_tracking(pp, teams, length, width)
        for r in by_match.get(m, []):
            found = _reception_point(ball, frames, r["pass_idx"], r["target_id"])
            if found is None:
                missing += 1
                continue
            _, ef = found
            fr = frames.get(ef, {})
            b0 = ball.get(ef)
            if not fr or b0 is None:
                missing += 1
                continue
            side = teams.get(r["target_id"])
            opps = [pos for pid, pos in fr.items() if teams.get(pid) != side]
            if not opps:
                missing += 1
                continue
            scored.append((r, _nearest(opps, b0)))
    print(f"scored={len(scored)} missing={missing}")

    def zone(x):
        return "def" if x < 35.0 else ("mid" if x < 70.0 else "att")

    cells = {}
    for r, before in scored:
        cells.setdefault((zone(r["recept_x_m"]), r["controlled"]), []).append(
            (r, before)
        )
    print("cell: n, med_delta, med_b, q90_b, med_c")
    for key in sorted(cells):
        sub = cells[key]
        X = [[1.0, b, 1.0 if r["hold_s"] < 3.0 else 0.0] for r, b in sub]
        y = [r["delta_press_m"] for r, _ in sub]
        import statistics

        bm = _qfit(X, y, 0.5)
        bq = _qfit(X, y, 0.9)
        print(
            f"{key}: n={len(sub)} med={statistics.median(y):+.2f} "
            f"med_b={bm[1]:+.3f} q90_b={bq[1]:+.3f} med_c={bm[2]:+.3f}"
        )
    X = [[1.0, b, 1.0 if r["hold_s"] < 3.0 else 0.0] for r, b in scored]
    y = [r["delta_press_m"] for r, _ in scored]
    bm = _qfit(X, y, 0.5)
    bq = _qfit(X, y, 0.9)
    print(f"pooled: n={len(scored)} med_b={bm[1]:+.3f} q90_b={bq[1]:+.3f}")


if __name__ == "__main__":
    main()
