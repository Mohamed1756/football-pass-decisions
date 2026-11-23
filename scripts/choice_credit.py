"""Branch credit readout: one row per freeze spending all six gates.

Join choice-sets to retention on (match, pass_idx, target_id); replay
frozen margins per viable outlet (consistency gate +-0.001 vs banked);
value via outlet_value_fitted with loosen 1.0 and territory attack sign
(3 m margin gate, ambiguous cells dropped with a count). Prints one line
per freeze plus aggregate tables. Read-only; deterministic.
"""

import statistics
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
RET_PATH = "data/pooled/idsse_retention_labeled.pkl"
MATCHES = ["J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WQQ", "J03WR9", "J03WPY"]


def _zone(x_m):
    return "def" if x_m < 35.0 else ("mid" if x_m < 70.0 else "att")


def main() -> None:
    import pickle

    rows = pickle.load(open(POOL_PATH, "rb"))
    ret = pickle.load(open(RET_PATH, "rb"))
    rx = {(r["match"], r["pass_idx"], r["target_id"]): r for r in ret}
    store = {}
    cuts = {}
    for m in MATCHES:
        c = "000001" if m in ("J03WMX", "J03WN1") else "000002"
        base = "/tmp/idsse_raw/DFL"
        mp = f"{base}_02_01_matchinformation_DFL-COM-{c}_DFL-MAT-{m}.xml"
        pp = f"{base}_04_03_positions_raw_observed_DFL-COM-{c}_DFL-MAT-{m}.xml"
        length, width, teams, _names = _load_roster(mp)
        frames, ball, stamps = _read_tracking(pp, teams, length, width)
        store[m] = (frames, ball, teams)
        ordered = sorted(stamps)
        gaps = [
            (stamps[ordered[i + 1]] - stamps[ordered[i]], ordered[i + 1])
            for i in range(len(ordered) - 1)
        ]
        cuts[m] = max(gaps)[1] if gaps else 0
    attack = {}
    dropped_cells = 0
    for m in MATCHES:
        _frames, _ball, teams = store[m]
        for per in (1, 2):
            for side in ("home", "away"):
                xs = [
                    rx[(r["match"], r["pass_idx"], r["target_id"])]["recept_x_m"]
                    for r in rows
                    if r["match"] == m
                    and (r["pass_idx"] < cuts[m]) == (per == 1)
                    and teams.get(r["target_id"]) == side
                ]
                if not xs:
                    dropped_cells += 1
                    continue
                mu = statistics.mean(xs)
                if abs(mu - 52.5) < 3.0:
                    dropped_cells += 1
                    continue
                attack[(m, per, side)] = 1.0 if mu > 52.5 else -1.0
    print(f"attack cells: {len(attack)} kept, {dropped_cells} ambiguous-dropped")

    maxdiff = 0.0
    dropped = 0
    out_rows = []
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
            dropped += 1
            continue
        mates = {pid: p for pid, p in frame.items() if teams.get(pid) == side}
        opps = {pid: p for pid, p in frame.items() if teams.get(pid) != side}
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
        vals = []
        vi = []
        ok = True
        for tid, pid in enumerate(r["outlet_pids"]):
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
            cp = fitted_control_prob(ready.post_cushion_s(res.margin_s))
            vals.append(
                outlet_value_fitted(cp, res.intercept_m.x, atk, loosen_prob=1.0)
            )
            vi.append(pid)
        if not ok or r["target_id"] not in vi:
            dropped += 1
            continue
        ci = vi.index(r["target_id"])
        best = max(vals)
        mean_v = sum(vals) / len(vals)
        rb = rx[(r["match"], r["pass_idx"], r["target_id"])]
        out_rows.append(
            {
                "match": m,
                "pass_idx": r["pass_idx"],
                "zone": _zone(rb["recept_x_m"]),
                "n_viable": r["n_viable"],
                "entropy_bits": r["entropy_bits"],
                "pre_press_m": rb.get("pre_press_m"),
                "pre_sep_vel": rb.get("pre_sep_vel"),
                "credit": round(vals[ci] - mean_v, 4),
                "regret": round(best - vals[ci], 4),
                "value_r0": ci
                == sorted(range(len(vals)), key=lambda i: vals[i], reverse=True)[0],
                "margin_r0": ci == r["chosen_rank"],
                "cushion_s": rb.get("cushion_s"),
                "controlled": rb["controlled"],
                "b_resid": round(
                    float(rb["controlled"]) - fitted_control_prob(rb["cushion_s"]), 4
                )
                if rb.get("cushion_s") is not None
                else None,
                "hold_s": rb.get("hold_s"),
                "hold_exit": rb.get("hold_exit"),
                "delta_press_m": rb.get("delta_press_m"),
                "delta_compact_m": rb.get("delta_compact_m"),
                "marking_dist_m": rb.get("marking_dist_m"),
            }
        )
    print(f"replay maxdiff={maxdiff:.4f} rows={len(out_rows)} dropped={dropped}")
    for o in out_rows[:5]:
        print(o)
    import collections

    bins = {"<=7": (0, 7), "8": (8, 8), "9": (9, 9), ">=10": (10, 99)}
    for name, (lo, hi) in bins.items():
        sub = [o for o in out_rows if lo <= o["n_viable"] <= hi]
        mc = statistics.mean(o["credit"] for o in sub)
        mr = statistics.mean(o["regret"] for o in sub)
        print(f"load {name}: n={len(sub)} mean_credit={mc:.4f} mean_regret={mr:.4f}")
    zs = collections.Counter(o["zone"] for o in out_rows)
    print("zones:", dict(sorted(zs.items())))
    br = [o["b_resid"] for o in out_rows if o["b_resid"] is not None]
    print(f"b_resid: n={len(br)} mean={statistics.mean(br):+.4f}")
    nv = sum(1 for o in out_rows if o["value_r0"])
    nm = sum(1 for o in out_rows if o["margin_r0"])
    print(
        f"identity: value_r0={nv}/{len(out_rows)}={nv / len(out_rows):.3f} margin_r0={nm}/{len(out_rows)}={nm / len(out_rows):.3f}"
    )


if __name__ == "__main__":
    main()
