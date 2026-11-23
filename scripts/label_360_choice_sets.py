"""Bank per-pass full choice sets from StatsBomb 360 freeze frames.

Raw prerequisite: event + three-sixty JSON per match (StatsBomb Open
Data, fetchable; La Liga 2020/21 ids in scripts, 35 matches). For each
ground pass with a named recipient, an outcome, and a freeze frame:
every in-frame teammate is an outlet (actor excluded), scored with
frozen arrival margins against in-frame opponents; the chosen outlet is
the nearest teammate to the pass end point, distance banked as the
misattribution audit. Frozen convention throughout (360 snapshots carry
no velocities; opponent sets are in-frame only, stated alongside the
calibration's own in-frame limitation). Run on demand, not in CI. CI
pins the banked file instead.
"""

import glob
import os
import sys

sys.path.insert(0, ".")

from src.core.geometry import PitchPoint
from src.io.three_sixty import (
    RECIPIENT_VERIFY_M,
    _read_freeze,
    _read_passes,
    choose_outlet,
)
from src.models.formation.mechanism import affordance_volume
from src.models.pressing.arrival import arrival_margin
from src.models.pressing.calibration import rank_outlets
from src.models.pressing.readiness import receiver_readiness
from src.models.pressing.types import PressingActor
from src.models.retention.mechanism import fitted_control_prob
from src.models.value_surface import outlet_value_fitted

RAW_DIR = "/tmp/sb360_1190"
POOL_PATH = "data/pooled/sb360_laliga_choice_sets.pkl"


def main() -> None:
    ev_paths = sorted(glob.glob(os.path.join(RAW_DIR, "events-*.json")))
    print(f"matches: {len(ev_paths)}")
    import statistics

    terr = {}
    for epath in ev_paths:
        mid0 = os.path.basename(epath).split("-")[1].split(".")[0]
        for p in _read_passes(epath):
            terr.setdefault((mid0, p.period, p.passer_team), []).append(p.end_pos_m[0])
    attack, dropped_cells = {}, 0
    for key, xs in terr.items():
        mu = statistics.mean(xs)
        if abs(mu - 52.5) < 3.0:
            dropped_cells += 1
            continue
        attack[key] = 1.0 if mu > 52.5 else -1.0
    print(f"attack cells: {len(attack)} kept, {dropped_cells} ambiguous-dropped")
    all_rows = []
    counts = {
        "no_freeze": 0,
        "no_outlet": 0,
        "unverified": 0,
        "kept": 0,
        "unscorable": 0,
    }
    for epath in ev_paths:
        mid = os.path.basename(epath).split("-")[1].split(".")[0]
        fpath = os.path.join(RAW_DIR, f"three-sixty-{mid}.json")
        if not os.path.exists(fpath):
            counts["no_freeze"] += 1
            continue
        freeze = _read_freeze(fpath)
        passes = _read_passes(epath)
        for p in passes:
            frame = freeze.get(p.event_uuid)
            if not frame:
                counts["no_freeze"] += 1
                continue
            mates = [m for m in frame if m.is_mate and not m.is_actor]
            opps = [m for m in frame if not m.is_mate]
            if not mates or not opps:
                counts["no_outlet"] += 1
                continue
            ci, dist = choose_outlet(mates, p.end_pos_m)
            if ci is None:
                counts["no_outlet"] += 1
                continue
            verify_ok = dist <= RECIPIENT_VERIFY_M
            if not verify_ok:
                counts["unverified"] += 1
            outlet_idx = list(range(len(mates)))
            opp_actors = [
                PressingActor(
                    track_id=tid,
                    team_id="opp",
                    pos_m=PitchPoint(*m.pos_m),
                    provider_id=f"o{tid}",
                )
                for tid, m in enumerate(opps)
            ]
            passer_pos = PitchPoint(*p.passer_pos_m)
            actor = next((m for m in frame if m.is_actor), None)
            if actor is not None:
                passer_pos = PitchPoint(*actor.pos_m)
            margins = []
            intercepts = []
            for tid, mi in enumerate(outlet_idx):
                m = mates[mi]
                rec = PressingActor(
                    track_id=tid,
                    team_id=p.passer_team,
                    pos_m=PitchPoint(*m.pos_m),
                    provider_id=f"r{tid}",
                )
                res = arrival_margin(rec, opp_actors, passer_pos)
                margins.append(res.margin_s)
                intercepts.append(
                    (res.intercept_m.x, res.intercept_m.y)
                    if res.intercept_m is not None
                    else None
                )
            if all(not m > -99.0 for m in margins):
                counts["unscorable"] += 1
                continue
            atk = attack.get((mid, p.period, p.passer_team))
            values = []
            for mgn, ix in zip(margins, intercepts):
                if not mgn > 0.0 or ix is None or atk is None:
                    values.append(None)
                    continue
                rec = PressingActor(
                    track_id=0,
                    team_id=p.passer_team,
                    pos_m=PitchPoint(*p.passer_pos_m),
                    provider_id="v",
                )
                ready = receiver_readiness(rec, passer_pos)
                cp = fitted_control_prob(ready.post_cushion_s(mgn))
                values.append(outlet_value_fitted(cp, ix[0], atk, loosen_prob=1.0))
            ranks = rank_outlets(margins)
            av = affordance_volume(margins)
            all_rows.append(
                {
                    "match": mid,
                    "event_uuid": p.event_uuid,
                    "period": p.period,
                    "complete": p.complete,
                    "n_outlets": len(outlet_idx),
                    "n_viable": av.n_viable,
                    "entropy_bits": av.entropy_bits,
                    "effective_options": av.effective_options,
                    "chosen_idx": ci,
                    "chosen_rank": ranks[ci].rank,
                    "chosen_margin": margins[ci],
                    "chosen_dist_m": dist,
                    "verify_ok": verify_ok,
                    "margins": margins,
                    "values": values,
                    "attack_sign": atk,
                    "passer_team": p.passer_team,
                    "timestamp_s": p.timestamp_s,
                }
            )
            counts["kept"] += 1
    print(counts)
    import pickle

    with open(POOL_PATH, "wb") as f:
        pickle.dump(all_rows, f)
    print(f"banked {len(all_rows)} sets -> {POOL_PATH}")
    if all_rows:
        import statistics as _s

        print("verify dist p50=%.1f" % _s.median(r["chosen_dist_m"] for r in all_rows))


if __name__ == "__main__":
    main()
