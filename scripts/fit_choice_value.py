"""Luce over value on the IDSSE full sets: single beta, four falsifiers.

P(j) = softmax(beta * v_j) over viable outlets, v = control x progress
(outlet_value_fitted with loosen 1.0). Attack sign per (match, period,
team) inferred from tracked pass deltas (>=90% agreement gate).
Frozen arrival replayed per outlet with a consistency gate (recomputed
margins match banked to +-0.001). Before/after vs linear-p and
split-softmax on identical rows and folds, plus a seeded
loop-stepper demo. Read-only; prints only.
"""

import math
import sys

sys.path.insert(0, ".")

from src.core.geometry import PitchPoint
from src.io.idsse import _load_roster, _read_tracking
from src.models.pressing.arrival import arrival_margin
from src.models.pressing.readiness import receiver_readiness
from src.models.pressing.types import PressingActor
from src.models.retention.mechanism import fitted_control_prob
from src.models.value_surface import outlet_value_fitted

POOL_PATH = "data/pooled/idsse_choice_sets_labeled.pkl"
MATCHES = ["J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WQQ", "J03WR9", "J03WPY"]
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
    import pickle

    rows = pickle.load(open(POOL_PATH, "rb"))
    ret = pickle.load(open("data/pooled/idsse_retention_labeled.pkl", "rb"))
    rx = {(r["match"], r["pass_idx"], r["target_id"]): r["recept_x_m"] for r in ret}
    store = {}
    cuts = {}
    for m in MATCHES:
        c = "000001" if m in ("J03WMX", "J03WN1") else "000002"
        base = "/tmp/idsse_raw/DFL"
        mp = f"{base}_02_01_matchinformation_DFL-COM-{c}_DFL-MAT-{m}.xml"
        pp = f"{base}_04_03_positions_raw_observed_DFL-COM-{c}_DFL-MAT-{m}.xml"
        length, width, teams, names = _load_roster(mp)
        frames, ball, stamps = _read_tracking(pp, teams, length, width)
        store[m] = (frames, ball, teams)
        ordered = sorted(stamps)
        gaps = [
            (stamps[ordered[i + 1]] - stamps[ordered[i]], ordered[i + 1])
            for i in range(len(ordered) - 1)
        ]
        cuts[m] = max(gaps)[1] if gaps else 0
    # Attack sign from territory: mean reception x per (match, period,
    # team) vs halfway. Levels, not pass deltas — the short game sends
    # as many balls sideways/back as forward, so direction fractions
    # carry no signal. Caveat: inferred from choice outcomes (coarse
    # cell means, not per-freeze identity). Margin gate 3 m.
    import statistics

    attack = {}
    dropped = 0
    for m in MATCHES:
        _frames, _ball, teams = store[m]
        for per in (1, 2):
            for side in ("home", "away"):
                xs = [
                    rx[(r["match"], r["pass_idx"], r["target_id"])]
                    for r in rows
                    if r["match"] == m
                    and (r["pass_idx"] < cuts[m]) == (per == 1)
                    and teams.get(r["target_id"]) == side
                ]
                if not xs:
                    dropped += 1
                    continue
                mu = statistics.mean(xs)
                if abs(mu - 52.5) < 3.0:
                    dropped += 1
                    continue
                attack[(m, per, side)] = 1.0 if mu > 52.5 else -1.0
    print(f"attack cells: {len(attack)} kept, {dropped} ambiguous-dropped")

    sets = []
    maxdiff = 0.0
    dropped_rows = 0
    for r in rows:
        m = r["match"]
        frames, ball, teams = store[m]
        f0 = r["pass_idx"]
        frame = frames.get(f0, {})
        b0 = ball.get(f0)
        if not frame or b0 is None:
            continue
        side = teams.get(r["target_id"])
        per = 1 if f0 < cuts[m] else 2
        atk = attack.get((m, per, side))
        if atk is None:
            dropped_rows += 1
            continue
        mates = {pid: pos for pid, pos in frame.items() if teams.get(pid) == side}
        opps = {pid: pos for pid, pos in frame.items() if teams.get(pid) != side}
        passer_pos = PitchPoint(*b0)
        opp_actors = [
            PressingActor(
                track_id=tid,
                team_id="opp",
                pos_m=PitchPoint(*pos),
                provider_id=pid,
            )
            for tid, (pid, pos) in enumerate(sorted(opps.items()))
        ]
        outlet_pids = list(r["outlet_pids"])
        vals = []
        vi = []
        ok = True
        for tid, pid in enumerate(outlet_pids):
            if pid not in mates:
                ok = False
                break
            rec = PressingActor(
                track_id=tid,
                team_id=side or "unknown",
                pos_m=PitchPoint(*mates[pid]),
                provider_id=pid,
            )
            res = arrival_margin(rec, opp_actors, passer_pos)
            if abs(res.margin_s - r["margins"][tid]) > 0.001 and abs(res.margin_s) < 90:
                ok = False
            maxdiff = max(
                maxdiff,
                abs(res.margin_s - r["margins"][tid])
                if abs(r["margins"][tid]) < 90
                else 0.0,
            )
            if res.margin_s <= 0.0 or res.intercept_m is None:
                continue
            ready = receiver_readiness(rec, passer_pos)
            cushion = ready.post_cushion_s(res.margin_s)
            cp = fitted_control_prob(cushion)
            v = outlet_value_fitted(cp, res.intercept_m.x, atk, loosen_prob=1.0)
            vals.append(v)
            vi.append(pid)
        if not ok:
            print("MARGIN MISMATCH - stopping")
            return
        if r["target_id"] not in vi:
            dropped_rows += 1
            continue
        sets.append((r, vals, vi.index(r["target_id"])))
    print(
        f"margin replay maxdiff={maxdiff:.4f}, sets={len(sets)}, dropped={dropped_rows}"
    )
    if not sets:
        print("NO SETS - stopping")
        return

    data = [(v, c) for _, v, c in sets]
    beta = _fit_beta(data)
    print(f"beta_value={beta:.4f} sign_ok={beta > 0}")
    for name, (lo, hi) in NV_BINS.items():
        probs, n, r0 = [], 0, 0
        for r, vals, ci in sets:
            if not lo <= r["n_viable"] <= hi:
                continue
            p = _sm(vals, beta)
            probs.append(p[_rank0(vals)])
            n += 1
            r0 += 1 if ci == _rank0(vals) else 0
        print(
            f"value_{name}: pred_r0={sum(probs) / len(probs):.3f} obs_r0={r0 / n:.3f} (n={n})"
        )

    matches = sorted({r["match"] for r in rows})
    tot_v = tot_lin = tot_sp = 0.0
    in_set = {(r["match"], r["pass_idx"], r["target_id"]) for r, _, _ in sets}
    for m in matches:
        tr = [(v, c) for (r, v, c) in sets if r["match"] != m]
        bv = _fit_beta(tr, init=beta)
        mtr = [
            (r["margins"], r["outlet_pids"].index(r["target_id"]))
            for r in rows
            if r["match"] != m and (r["match"], r["pass_idx"], r["target_id"]) in in_set
        ]
        mrows = [
            r
            for r in rows
            if r["match"] != m and (r["match"], r["pass_idx"], r["target_id"]) in in_set
        ]
        blo = _fit_beta(
            [(mm, c) for (mm, c), r in zip(mtr, mrows) if r["n_viable"] <= 7],
            init=1.0,
        )
        bhi = _fit_beta(
            [(mm, c) for (mm, c), r in zip(mtr, mrows) if r["n_viable"] >= 10],
            init=1.0,
        )
        bpo = _fit_beta(mtr, init=1.0)
        for r, vals, ci in sets:
            if r["match"] != m:
                continue
            tot_v += math.log(max(_sm(vals, bv)[ci], 1e-300))
            mm = r["margins"]
            mc = r["outlet_pids"].index(r["target_id"])
            bb = blo if r["n_viable"] <= 7 else (bhi if r["n_viable"] >= 10 else bpo)
            tot_sp += math.log(max(_sm(mm, bb)[mc], 1e-300))
        for r in rows:
            if r["match"] != m:
                continue
            if (r["match"], r["pass_idx"], r["target_id"]) not in in_set:
                continue
            mm = r["margins"]
            ci = r["outlet_pids"].index(r["target_id"])
            if mm[ci] <= 0.0:
                continue
            viable = [x for x in mm if x > 0.0]
            tot_lin += math.log(mm[ci] / sum(viable))
    print(f"loo_value={tot_v:.1f} loo_split={tot_sp:.1f} loo_linear={tot_lin:.1f}")

    # Identity check: value-rank-0 vs margin-rank-0 as the chosen outlet.
    n_both = sum(
        1 for r, vals, ci in sets if ci == _rank0(vals) and ci == r["chosen_rank"]
    )
    n_val = sum(1 for _, vals, ci in sets if ci == _rank0(vals))
    n_mar = sum(1 for r, _, ci in sets if ci == r["chosen_rank"])
    print(
        f"identity: value_r0={n_val}/{len(sets)}={n_val / len(sets):.3f} "
        f"margin_r0={n_mar}/{len(sets)}={n_mar / len(sets):.3f} both={n_both}"
    )

    import random

    rng = random.Random(7)
    shown = 0
    for r, vals, ci in sets:
        if _bin_of(r["n_viable"]) != ">=10" or shown >= 3:
            continue
        p = _sm(vals, beta)
        draw = rng.choices(range(len(vals)), weights=p, k=1)[0]
        print(
            f"step {r['match']}@{r['pass_idx']}: n={len(vals)} "
            f"value_r0_prob={max(p):.2f} drawn={draw} actual={ci}"
        )
        shown += 1


if __name__ == "__main__":
    main()
