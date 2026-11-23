"""Fit noisy-race psychometric on WC2022; judge on held-out leagues.

P(fail|m) = logistic((tau - m) / sigma), MLE on the 41,561 WC2022
(margin, complete) rows (2x2 Newton, concave). Both models frozen
from WC2022 only: the logistic vs the pinned decile edges + rates.
Predictive NLL on Euro2020 / LaLiga / Euro2024, same frozen rows the
replication section uses. Read-only on the banked pool.
"""

import math
import pickle
import sys

sys.path.insert(0, ".")

from src.models.pressing.calibration import (
    DECILE_INCOMPLETION_RATE,
    margin_decile,
)

POOL_PATH = "data/pooled/frozen_five_leagues.pkl"
JUDGES = ("euro2020", "laliga", "euro2024")


def _fit_beta(rows):
    b0, b1 = 0.0, 2.0
    data = [(r["margin"], 1.0 if r["complete"] else 0.0) for r in rows]
    for _ in range(100):
        g0 = g1 = h00 = h01 = h11 = 0.0
        for m, y in data:
            z = min(500.0, max(-500.0, b0 + b1 * m))
            p = 1.0 / (1.0 + math.exp(z))  # P(fail)
            w = p * (1.0 - p)
            r = p - (1.0 - y)  # d(neg-loglik)/db direction; Newton descends
            g0 += r
            g1 += r * m
            h00 -= w
            h01 -= w * m
            h11 -= w * m * m
        det = h00 * h11 - h01 * h01
        if det == 0.0:
            break
        s0 = (h11 * g0 - h01 * g1) / det
        s1 = (-h01 * g0 + h00 * g1) / det
        b0 -= s0
        b1 -= s1
        if abs(s0) + abs(s1) < 1e-12:
            break
    return b0, b1


def _pfail(m, b0, b1):
    z = min(500.0, max(-500.0, b0 + b1 * m))
    return 1.0 / (1.0 + math.exp(z))


def _nll(rows, prob):
    ll = 0.0
    for r in rows:
        p = min(1.0 - 1e-12, max(1e-12, prob(r["margin"])))
        ll += math.log(1.0 - p) if r["complete"] else math.log(p)
    return -ll


def main() -> None:
    five = pickle.load(open(POOL_PATH, "rb"))
    wc = five["wc2022"]
    b0, b1 = _fit_beta(wc)
    tau, sigma = -b0 / b1, 1.0 / b1
    print(f"beta0={b0:.4f} beta1={b1:.4f} tau={tau:.3f}s sigma={sigma:.3f}s")
    print("sign_ok=" + str(b1 > 0) + " tau_near_viability=" + str(abs(tau) <= 0.5))

    for lg in ("wc2022",) + JUDGES + ("wwc2023",):
        rows = five[lg]
        nll_log = _nll(rows, lambda m: _pfail(m, b0, b1))
        nll_dec = _nll(rows, lambda m: DECILE_INCOMPLETION_RATE[margin_decile(m) - 1])
        print(
            f"{lg}: n={len(rows)} nll_logistic={nll_log:.1f} nll_decile={nll_dec:.1f}"
        )

    for lg, rows in five.items():
        neg = [r for r in rows if r["margin"] < 0.0]
        f = sum(1 for r in neg if not r["complete"]) / len(neg) if neg else float("nan")
        print(f"{lg}: neg_margin n={len(neg)} fail_rate={f:.3f}")


if __name__ == "__main__":
    main()
