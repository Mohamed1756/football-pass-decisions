"""Fit uniform-mixture choice model on the IDSSE full sets.

P(j) = (1-lambda_b) * softmax(beta * m)_j + lambda_b / n,
beta shared, lambda_b per viable-size bin (overload rises with load).
Coordinate ascent (1-D Newton alternating beta | lambdas; lambdas via
logistic transform, unconstrained). Pre-registered falsifiers:
lambda monotone rising in load, gradient +-0.06 on all four bins,
beats linear AND split-beta out-of-sample (leave-one-match-out).
Read-only on the banked pool.
"""

import math
import pickle
import sys

sys.path.insert(0, ".")

POOL_PATH = "data/pooled/idsse_choice_sets_labeled.pkl"
NV_BINS = {"<=7": (0, 7), "8": (8, 8), "9": (9, 9), ">=10": (10, 99)}


def _bin_of(nv):
    for name, (lo, hi) in NV_BINS.items():
        if lo <= nv <= hi:
            return name
    raise ValueError(nv)


_BIDX = {"<=7": 0, "8": 1, "9": 2, ">=10": 3}


def _smax(margins, beta):
    m = max(margins)
    exps = [math.exp(beta * (x - m)) for x in margins]
    s = sum(exps)
    return [e / s for e in exps]


def _negll(params, data):
    # params: [beta, g_lo, g_8, g_9, g_hi], lambda = logistic(g).
    beta = params[0]
    ll = 0.0
    for margins, chosen, bname in data:
        lam = 1.0 / (1.0 + math.exp(-params[1 + _BIDX[bname]]))
        p = _smax(margins, beta)
        q = (1.0 - lam) * p[chosen] + lam / len(margins)
        ll += math.log(max(q, 1e-300))
    return -ll


def _fit(data, init_beta=1.0, iters=60):
    params = [init_beta, 0.0, 0.0, 0.0, 0.0]
    cur = _negll(params, data)
    for _ in range(iters):
        for j in range(5):
            # 1-D Newton with numeric gradient/Hessian, step-halved.
            h = 1e-5
            pj = list(params)
            pj[j] += h
            mj = list(params)
            mj[j] -= h
            g = (_negll(pj, data) - _negll(mj, data)) / (2 * h)
            h2 = (_negll(pj, data) - 2 * cur + _negll(mj, data)) / (h * h)
            if h2 <= 0:
                continue
            s = g / h2
            trial = list(params)
            trial[j] -= s
            t = _negll(trial, data)
            halv = 0
            while t >= cur and halv < 20:
                s *= 0.5
                trial = list(params)
                trial[j] -= s
                t = _negll(trial, data)
                halv += 1
            if t < cur:
                params, cur = trial, t
    beta = params[0]
    lams = {k: 1.0 / (1.0 + math.exp(-params[1 + v])) for k, v in _BIDX.items()}
    return beta, lams, cur


def _rank0_index(margins):
    return sorted(range(len(margins)), key=lambda i: margins[i], reverse=True)[0]


def main() -> None:
    rows = pickle.load(open(POOL_PATH, "rb"))
    data = [
        (
            r["margins"],
            r["outlet_pids"].index(r["target_id"]),
            _bin_of(r["n_viable"]),
        )
        for r in rows
    ]
    beta, lams, nll = _fit(data)
    print(f"beta={beta:.4f} " + " ".join(f"lam_{k}={v:.3f}" for k, v in lams.items()))
    print(f"in-sample nll={nll:.1f}")
    lo = [lams["<=7"], lams["8"], lams["9"], lams[">=10"]]
    print("lambda_ordered=" + str(all(a < b for a, b in zip(lo, lo[1:]))))

    for name in NV_BINS:
        probs, n, r0 = [], 0, 0
        lam = lams[name]
        for r in rows:
            if _bin_of(r["n_viable"]) != name:
                continue
            margins = r["margins"]
            ci = r["outlet_pids"].index(r["target_id"])
            r0i = _rank0_index(margins)
            p = _smax(margins, beta)
            probs.append((1.0 - lam) * p[r0i] + lam / len(margins))
            n += 1
            r0 += 1 if ci == r0i else 0
        print(
            f"mix_{name}: pred_r0={sum(probs) / len(probs):.3f} obs_r0={r0 / n:.3f} (n={n})"
        )

    # Out-of-sample vs split-beta and linear: LOO by match.
    sys.path.insert(0, "scripts")
    tot_mx = tot_sp = tot_lin = 0.0
    matches = sorted({r["match"] for r in rows})
    for m in matches:
        tr = [d for d, r in zip(data, rows) if r["match"] != m]
        te = [r for r in rows if r["match"] == m]
        bpo, _, _ = _fit(tr, init_beta=beta, iters=25)
        # split-beta refit on extremes for pooled comparison baseline
        blo = _fit_beta_simple([(mm, c) for mm, c, bn in tr if bn == "<=7"], init=bpo)
        bhi = _fit_beta_simple([(mm, c) for mm, c, bn in tr if bn == ">=10"], init=bpo)
        bm, lm, _ = _fit(tr, init_beta=beta, iters=25)
        for r in te:
            margins = r["margins"]
            ci = r["outlet_pids"].index(r["target_id"])
            lam = lm[_bin_of(r["n_viable"])]
            p = _smax(margins, bm)
            tot_mx += math.log(max((1 - lam) * p[ci] + lam / len(margins), 1e-300))
            bb = blo if r["n_viable"] <= 7 else (bhi if r["n_viable"] >= 10 else bpo)
            tot_sp += math.log(max(_smax(margins, bb)[ci], 1e-300))
            viable = [x for x in margins if x > 0.0]
            if margins[ci] > 0.0:
                tot_lin += math.log(margins[ci] / sum(viable))
    print(f"loo_mix={tot_mx:.1f} loo_split={tot_sp:.1f} loo_linear={tot_lin:.1f}")


def _fit_beta_simple(sets, init=1.0, iters=50):
    beta = init
    for _ in range(iters):
        g = h = 0.0
        for margins, chosen in sets:
            probs = _smax(margins, beta)
            mean = sum(p * x for p, x in zip(probs, margins))
            var = sum(p * (x - mean) ** 2 for p, x in zip(probs, margins))
            g += margins[chosen] - mean
            h -= var
        if h == 0.0:
            break
        step = g / h
        beta -= step
        if abs(step) < 1e-12:
            break
    return beta


if __name__ == "__main__":
    main()
