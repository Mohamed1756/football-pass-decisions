"""Choice eval on the banked LaLiga 360 full sets. Read-only; prints only.

Gradient by viable size, value-rank vs margin-rank identity, linear-p
vs value-softmax out-of-sample (leave-one-match-out, refit per fold).
Same bars, new pool: pre-registered identically to the IDSSE fit.
"""

import math
import pickle
import sys

sys.path.insert(0, ".")

POOL_PATH = "data/pooled/sb360_laliga_choice_sets.pkl"
NV_BINS = {"<=7": (0, 7), "8": (8, 8), "9": (9, 9), ">=10": (10, 99)}


def _sm(xs, beta):
    m = max(xs)
    exps = [math.exp(min(500.0, max(-500.0, beta * (x - m)))) for x in xs]
    s = sum(exps)
    return [e / s for e in exps]


def _fit_beta(sets, init=1.0, iters=80):
    beta = init
    for _ in range(iters):
        g = h = 0.0
        for xs, ch in sets:
            p = _sm(xs, beta)
            mean = sum(a * b for a, b in zip(p, xs))
            var = sum(a * (b - mean) ** 2 for a, b in zip(p, xs))
            g += xs[ch] - mean
            h -= var
        if h == 0.0:
            break
        step = g / h
        beta -= step
        if abs(step) < 1e-12:
            break
    return beta


def _rank0(xs):
    return sorted(range(len(xs)), key=lambda i: xs[i], reverse=True)[0]


def _bin_of(nv):
    for name, (lo, hi) in NV_BINS.items():
        if lo <= nv <= hi:
            return name
    raise ValueError(nv)


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--verified-only", action="store_true")
    args = ap.parse_args()
    rows = pickle.load(open(POOL_PATH, "rb"))
    if args.verified_only:
        rows = [r for r in rows if r["verify_ok"]]
        print(f"verified subset: n={len(rows)}")
    ok = [r for r in rows if r["verify_ok"]]
    print(f"verified={len(ok)} ({len(ok) / len(rows):.2f})")
    print("n_outlets mean=%.2f" % (sum(r["n_outlets"] for r in rows) / len(rows)))
    print("n_viable mean=%.2f" % (sum(r["n_viable"] for r in rows) / len(rows)))

    for name, (lo, hi) in NV_BINS.items():
        sub = [r for r in rows if lo <= r["n_viable"] <= hi]
        if not sub:
            print(f"bin {name}: n=0")
            continue
        r0 = sum(1 for r in sub if r["chosen_rank"] == 0)
        print(f"bin nv {name}: n={len(sub)} P(rank0)={r0 / len(sub):.3f}")

    # Identity: value-rank-0 vs margin-rank-0 among attack-mapped rows.
    have_v = [r for r in rows if any(v is not None for v in r["values"])]
    nv = sum(
        1
        for r in have_v
        if r["values"][_rank0([v if v is not None else -1 for v in r["values"]])]
        is not None
        and r["chosen_idx"] == _rank0([v if v is not None else -1 for v in r["values"]])
    )
    nm = sum(1 for r in have_v if r["chosen_rank"] == 0)
    print(
        f"identity: value_r0={nv}/{len(have_v)}={nv / len(have_v):.3f} margin_r0={nm}/{len(have_v)}={nm / len(have_v):.3f}"
    )

    # Linear-p vs value-softmax OOS on the same viable-chosen rows.
    comp = [
        r
        for r in rows
        if r["margins"][r["chosen_idx"]] > 0.0
        and r["attack_sign"] is not None
        and r["values"][r["chosen_idx"]] is not None
    ]
    print(f"comparison rows={len(comp)}")
    vall = [
        (
            [v for v in r["values"] if v is not None],
            [i for i, v in enumerate(r["values"]) if v is not None].index(
                r["chosen_idx"]
            ),
        )
        for r in comp
    ]
    bv_all = _fit_beta(vall, init=3.5)
    print(f"beta_value={bv_all:.4f} sign_ok={bv_all > 0}")
    for name, (lo, hi) in NV_BINS.items():
        probs, n, r0 = [], 0, 0
        for r in comp:
            if not lo <= r["n_viable"] <= hi:
                continue
            vals = [v for v in r["values"] if v is not None]
            ci = [i for i, v in enumerate(r["values"]) if v is not None].index(
                r["chosen_idx"]
            )
            p = _sm(vals, bv_all)
            probs.append(p[_rank0(vals)])
            n += 1
            r0 += 1 if ci == _rank0(vals) else 0
        if n:
            print(
                f"value_{name}: pred_r0={sum(probs) / len(probs):.3f} obs_r0={r0 / n:.3f} (n={n})"
            )
        else:
            print(f"value_{name}: n=0")
    matches = sorted({r["match"] for r in comp})
    tot_v = tot_lin = 0.0
    for m in matches:
        tr = [
            (
                [v for v in r["values"] if v is not None],
                [i for i, v in enumerate(r["values"]) if v is not None].index(
                    r["chosen_idx"]
                ),
            )
            for r in comp
            if r["match"] != m
        ]
        bv = _fit_beta(tr, init=3.5)
        for r in comp:
            if r["match"] != m:
                continue
            vals = [v for v in r["values"] if v is not None]
            ci = [i for i, v in enumerate(r["values"]) if v is not None].index(
                r["chosen_idx"]
            )
            tot_v += math.log(max(_sm(vals, bv)[ci], 1e-300))
            mm = r["margins"]
            tot_lin += math.log(mm[r["chosen_idx"]] / sum(x for x in mm if x > 0.0))
    print(f"loo_value={tot_v:.1f} loo_linear={tot_lin:.1f}")
    print("value_wins=" + str(tot_v > tot_lin))


if __name__ == "__main__":
    main()
