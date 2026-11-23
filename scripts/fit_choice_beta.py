"""Fit pooled Luce-McFadden beta on the banked IDSSE full sets.

P(j) = exp(beta * m_j) / sum_k exp(beta * m_k), frozen margins, one
pooled beta by MLE (1-D Newton, concave log-likelihood). Prints the
pre-registered falsifiers: sign, load-gradient reproduction,
softmax-vs-linear out-of-sample (leave-one-match-out log-likelihood),
and LOO-match beta stability. Read-only on the banked pool.
"""

import math
import pickle
import sys

sys.path.insert(0, ".")

POOL_PATH = "data/pooled/idsse_choice_sets_labeled.pkl"
NV_BINS = {"<=7": (0, 7), "8": (8, 8), "9": (9, 9), ">=10": (10, 99)}


def _softmax_probs(margins, beta):
    m = max(margins)
    exps = [math.exp(beta * (x - m)) for x in margins]
    s = sum(exps)
    return [e / s for e in exps]


def _loglik(beta, sets):
    ll = 0.0
    for margins, chosen in sets:
        ll += math.log(max(_softmax_probs(margins, beta)[chosen], 1e-300))
    return ll


def _fit_beta(sets, init=0.0, iters=50):
    beta = init
    for _ in range(iters):
        g = 0.0
        h = 0.0
        for margins, chosen in sets:
            probs = _softmax_probs(margins, beta)
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


def _rank0_index(margins):
    return sorted(range(len(margins)), key=lambda i: margins[i], reverse=True)[0]


def main() -> None:
    rows = pickle.load(open(POOL_PATH, "rb"))
    sets = [
        (r["margins"], r["outlet_pids"].index(r["target_id"]), r["match"]) for r in rows
    ]
    nflag = sum(1 for r in rows if r.get("passer_fallback"))
    print(f"sets={len(sets)} fallback_rows={nflag}")

    beta = _fit_beta([(m, c) for m, c, _ in sets])
    ll = _loglik(beta, [(m, c) for m, c, _ in sets])
    null = -sum(math.log(len(m)) for m, _, _ in sets)
    print(f"beta_pooled={beta:.4f} loglik={ll:.1f} null={null:.1f}")
    print("sign_ok=" + str(beta > 0))

    matches = sorted({m for _, _, m in sets})
    loo = {}
    for m in matches:
        sub = [(mm, c) for mm, c, mch in sets if mch != m]
        loo[m] = _fit_beta(sub, init=beta)
    print("loo_beta=" + ", ".join(f"{m}:{b:.4f}" for m, b in loo.items()))

    for name, (lo, hi) in NV_BINS.items():
        probs, n, r0 = [], 0, 0
        for r, (margins, chosen, _) in zip(rows, sets):
            if not lo <= r["n_viable"] <= hi:
                continue
            p = _softmax_probs(margins, beta)
            probs.append(p[_rank0_index(margins)])
            n += 1
            r0 += 1 if chosen == _rank0_index(margins) else 0
        print(
            f"bin_nv_{name}: pred_r0={sum(probs) / len(probs):.3f} obs_r0={r0 / n:.3f} (n={n})"
        )

    # Falsifier 3: softmax vs linear-p out-of-sample. Linear chooses among
    # viable outlets proportional to margin (no parameter); the one
    # non-viable-chosen row fits neither and is excluded from both.
    comp = [
        r for r in rows if r["margins"][r["outlet_pids"].index(r["target_id"])] > 0.0
    ]
    print(f"comparison_sets={len(comp)}")
    tot_sm = tot_lin = 0.0
    for m in matches:
        tr = [
            (r["margins"], r["outlet_pids"].index(r["target_id"]))
            for r in comp
            if r["match"] != m
        ]
        b = _fit_beta(tr, init=beta)
        for r in comp:
            if r["match"] != m:
                continue
            margins = r["margins"]
            ci = r["outlet_pids"].index(r["target_id"])
            tot_sm += math.log(max(_softmax_probs(margins, b)[ci], 1e-300))
            viable = [x for x in margins if x > 0.0]
            tot_lin += math.log(margins[ci] / sum(viable))
    print(f"loo_loglik_softmax={tot_sm:.1f} loo_loglik_linear={tot_lin:.1f}")
    print("linear_wins=" + str(tot_lin > tot_sm))

    # Split-beta: sensitivity falls with load. Fit on extreme bins only
    # (nv<=7 vs nv>=10; middle bins judge), pooled beta as init.
    lo_sets = [
        (r["margins"], r["outlet_pids"].index(r["target_id"]))
        for r in rows
        if r["n_viable"] <= 7
    ]
    hi_sets = [
        (r["margins"], r["outlet_pids"].index(r["target_id"]))
        for r in rows
        if r["n_viable"] >= 10
    ]
    b_lo = _fit_beta(lo_sets, init=beta)
    b_hi = _fit_beta(hi_sets, init=beta)
    print(
        f"split_beta low={b_lo:.4f} (n={len(lo_sets)}) high={b_hi:.4f} (n={len(hi_sets)})"
    )
    print("split_sign_ok=" + str(b_lo > 0 and b_hi > 0))
    print("split_ordered=" + str(b_lo > b_hi))
    for name, (lo, hi) in NV_BINS.items():
        probs, n, r0 = [], 0, 0
        for r in rows:
            if not lo <= r["n_viable"] <= hi:
                continue
            b = b_lo if r["n_viable"] <= 7 else (b_hi if r["n_viable"] >= 10 else beta)
            margins = r["margins"]
            ci = r["outlet_pids"].index(r["target_id"])
            r0i = _rank0_index(margins)
            probs.append(_softmax_probs(margins, b)[r0i])
            n += 1
            r0 += 1 if ci == r0i else 0
        print(
            f"split_{name}: pred_r0={sum(probs) / len(probs):.3f} obs_r0={r0 / n:.3f} (n={n})"
        )

    # Split vs pooled out-of-sample: LOO by match, split refit per fold.
    tot_sp = tot_po = 0.0
    for m in matches:
        tr = [
            (r, (r["margins"], r["outlet_pids"].index(r["target_id"])))
            for r in rows
            if r["match"] != m
        ]
        blo = _fit_beta([(mm, c) for r, (mm, c) in tr if r["n_viable"] <= 7], init=beta)
        bhi = _fit_beta(
            [(mm, c) for r, (mm, c) in tr if r["n_viable"] >= 10], init=beta
        )
        bpo = _fit_beta([(mm, c) for _, (mm, c) in tr], init=beta)
        for r in rows:
            if r["match"] != m:
                continue
            margins = r["margins"]
            ci = r["outlet_pids"].index(r["target_id"])
            b = blo if r["n_viable"] <= 7 else (bhi if r["n_viable"] >= 10 else bpo)
            tot_sp += math.log(max(_softmax_probs(margins, b)[ci], 1e-300))
            tot_po += math.log(max(_softmax_probs(margins, bpo)[ci], 1e-300))
    print(f"loo_loglik_split={tot_sp:.1f} loo_loglik_pooled={tot_po:.1f}")
    print("split_wins=" + str(tot_sp > tot_po))


if __name__ == "__main__":
    main()
