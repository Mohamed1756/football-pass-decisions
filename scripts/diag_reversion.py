"""Diagnostic: median delta_press on proxy-before + in-window indicator.

median(delta) = a + b*pre_press_m + c*I(hold<3s), per zone x control
cell (IRLS for L1). Null on b is -1 under independence (Oldham: the
-1 survives proxy noise; attenuation only shrinks deviations toward
it, so a slope clearly above -1 is conservative evidence of
persistence/relaxation). c absorbs the +3 s window artifact via the
banked hold_s. Read-only; kill-or-proceed for the receipt-level
re-bank.
"""

import pickle
import sys

sys.path.insert(0, ".")

POOL_PATH = "data/pooled/idsse_retention_labeled.pkl"


def _median_fit(X, y, iters=200):
    # IRLS for L1: weights 1/|resid|, closed-form WLS per step.
    import statistics

    b = [0.0, -1.0, 0.0]
    n, p = len(y), 3
    for _ in range(iters):
        r = [y[i] - sum(X[i][j] * b[j] for j in range(p)) for i in range(n)]
        w = [1.0 / max(abs(x), 1e-6) for x in r]
        # Solve (X'WX) b = X'Wy by Gaussian elimination on 3x3.
        A = [[0.0] * 4 for _ in range(3)]
        for i in range(n):
            for a in range(3):
                for c_ in range(3):
                    A[a][c_] += w[i] * X[i][a] * X[i][c_]
                A[a][3] += w[i] * X[i][a] * y[i]
        for col in range(3):
            piv = max(range(col, 3), key=lambda q: abs(A[q][col]))
            A[col], A[piv] = A[piv], A[col]
            if abs(A[col][col]) < 1e-12:
                break
            for q in range(3):
                if q != col:
                    f = A[q][col] / A[col][col]
                    for c_ in range(col, 4):
                        A[q][c_] -= f * A[col][c_]
        nb = [A[a][3] / A[a][a] if abs(A[a][a]) > 1e-12 else b[a] for a in range(3)]
        if max(abs(x - y_) for x, y_ in zip(nb, b)) < 1e-9:
            b = nb
            break
        b = nb
    med = statistics.median(
        [y[i] - sum(X[i][j] * b[j] for j in range(p)) for i in range(n)]
    )
    b[0] += med
    return b


def main() -> None:
    rows = pickle.load(open(POOL_PATH, "rb"))
    have = [r for r in rows if r.get("pre_press_m") is not None]
    print(f"rows={len(have)} (1 dropped: incomplete -5 s track)")

    def zone(x):
        return "def" if x < 35.0 else ("mid" if x < 70.0 else "att")

    cells = {}
    for r in have:
        cells.setdefault((zone(r["recept_x_m"]), r["controlled"]), []).append(r)
    print("cell (zone, controlled): n, median_delta, b_proxy, c_inwindow")
    for key in sorted(cells):
        sub = cells[key]
        X = [[1.0, r["pre_press_m"], 1.0 if r["hold_s"] < 3.0 else 0.0] for r in sub]
        y = [r["delta_press_m"] for r in sub]
        import statistics

        a, b, c = _median_fit(X, y)
        print(
            f"{key}: n={len(sub)} med={statistics.median(y):+.2f} "
            f"b={b:+.3f} (null -1) c={c:+.3f}"
        )
    X = [[1.0, r["pre_press_m"], 1.0 if r["hold_s"] < 3.0 else 0.0] for r in have]
    y = [r["delta_press_m"] for r in have]
    a, b, c = _median_fit(X, y)
    print(f"pooled: n={len(have)} b={b:+.3f} c={c:+.3f}")


if __name__ == "__main__":
    main()
