"""Label retention touches + gate-0/1 windows on raw IDSSE tracking.

Raw prerequisite: the 7 matches at /tmp/idsse_raw (HuggingFace
`pysport/idsse-data`, re-downloadable). Reads them, applies the touch
rule at receipt+1 s, banks (cushion, marking, controlled, deltas,
pre-freeze, hold) rows. Slow (~2 min, 400 MB XML): run on demand,
not in CI. CI pins the banked file instead.
"""

import pickle
import sys

sys.path.insert(0, ".")

from src.core.geometry import PitchPoint
from src.io.idsse import (
    _load_roster,
    _read_passes,
    _read_tracking,
    _reception_point,
    _velocity,
    reception_window,
)
from src.models.pressing.arrival import arrival_margin
from src.models.pressing.readiness import receiver_readiness
from src.models.pressing.types import PressingActor

MATCHES = ["J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WQQ", "J03WR9", "J03WPY"]


def main() -> None:
    rows = []
    for m in MATCHES:
        c = "000001" if m in ("J03WMX", "J03WN1") else "000002"
        base = "/tmp/idsse_raw/DFL"
        mp = f"{base}_02_01_matchinformation_DFL-COM-{c}_DFL-MAT-{m}.xml"
        pp = f"{base}_04_03_positions_raw_observed_DFL-COM-{c}_DFL-MAT-{m}.xml"
        ep = f"{base}_03_02_events_raw_DFL-COM-{c}_DFL-MAT-{m}.xml"
        length, width, teams, names = _load_roster(mp)
        frames, ball, stamps = _read_tracking(pp, teams, length, width)
        passes = _read_passes(ep, stamps, teams, names)
        from src.io.idsse import _read_events_raw
        from src.models.attempt.mechanism import next_event

        raw_events = _read_events_raw(ep, stamps)
        kept = 0
        for p in passes:
            found = _reception_point(ball, frames, p.start_frame, p.target_id)
            if found is None:
                continue
            end_pos, end_frame = found
            hold = next_event(raw_events, end_frame)
            w = reception_window(ball, frames, end_frame, p.target_id)
            if w.ball_plus1 is None or w.receiver_plus1 is None:
                continue
            rec = None
            opps = []
            for tid, (pid, pos) in enumerate(frames.get(p.start_frame, {}).items()):
                vel = _velocity(frames, p.start_frame, pid)
                a = PressingActor(
                    track_id=tid,
                    team_id=teams.get(pid, "unknown"),
                    pos_m=PitchPoint(*pos),
                    vel_ms=vel,
                    provider_id=pid,
                )
                if pid == p.target_id:
                    rec = a
                elif teams.get(pid) != teams.get(p.target_id):
                    opps.append(a)
            if rec is None:
                continue
            res = arrival_margin(
                rec,
                opps,
                p.passer_pos_m,
                live_pressers=True,
                measured=(end_pos, (end_frame - p.start_frame) / 25.0),
            )
            ready = receiver_readiness(rec, p.passer_pos_m)
            from src.io.idsse import STRUCT_WINDOW_FRAMES, FREEZE_WINDOW_FRAMES
            from src.models.formation.mechanism import formation_window
            from src.models.retention.mechanism import label_touch
            from src.models.structure.mechanism import structure_delta

            f3 = end_frame + STRUCT_WINDOW_FRAMES  # receipt+3 s
            b0 = ball.get(end_frame)
            b3 = ball.get(f3)
            r0 = frames.get(end_frame, {}).get(p.target_id)
            r3 = frames.get(f3, {}).get(p.target_id)
            delta = None
            if b0 is not None and b3 is not None and r0 is not None and r3 is not None:
                mates_b = {
                    pid: pos
                    for pid, pos in frames.get(end_frame, {}).items()
                    if teams.get(pid) == teams.get(p.target_id) and pid != p.target_id
                }
                mates_a = {
                    pid: pos
                    for pid, pos in frames.get(f3, {}).items()
                    if teams.get(pid) == teams.get(p.target_id) and pid != p.target_id
                }
                opps_b = {
                    pid: pos
                    for pid, pos in frames.get(end_frame, {}).items()
                    if teams.get(pid) != teams.get(p.target_id)
                }
                opps_a = {
                    pid: pos
                    for pid, pos in frames.get(f3, {}).items()
                    if teams.get(pid) != teams.get(p.target_id)
                }
                mates_b[p.target_id] = r0
                mates_a[p.target_id] = r3
                d = structure_delta(b0, b3, mates_b, mates_a, opps_b, opps_a)
                delta = (
                    d.press_access_delta_m,
                    d.compactness_delta_m,
                )
            pre = None
            f0 = p.start_frame
            f5 = f0 - FREEZE_WINDOW_FRAMES  # pass -5 s
            if f5 in frames and f0 in frames and ball.get(f0) is not None:
                mates_f = {
                    pid: pos
                    for pid, pos in frames.get(f0, {}).items()
                    if teams.get(pid) == teams.get(p.target_id)
                }
                opps_f = {
                    pid: pos
                    for pid, pos in frames.get(f0, {}).items()
                    if teams.get(pid) != teams.get(p.target_id)
                }
                tracks: dict = {}
                ok = True
                for pid in mates_f:
                    track = []
                    for f in range(f5, f0 + 1, 25):
                        pos = frames.get(f, {}).get(pid)
                        if pos is None:
                            ok = False
                            break
                        track.append(pos)
                    if not ok:
                        break
                    tracks[pid] = track
                if ok and mates_f and opps_f:
                    fw = formation_window(ball.get(f0), mates_f, opps_f, tracks)
                    pre = (
                        fw.press_access_at_freeze_m,
                        fw.separation_velocity_ms,
                    )
            rows.append(
                {
                    "match": m,
                    "pass_idx": p.start_frame,
                    "target_id": p.target_id,
                    "passer": p.passer,
                    "complete": p.complete,
                    "margin_s": res.margin_s,
                    "t_ball_s": res.t_ball_s,
                    "cushion_s": ready.post_cushion_s(res.margin_s),
                    "marking_dist_m": w.marking_dist_m,
                    "controlled": label_touch(w.ball_plus1, w.receiver_plus1),
                    "recept_x_m": round(end_pos.x, 2),
                    "recept_y_m": round(end_pos.y, 2),
                    "delta_press_m": delta[0] if delta else None,
                    "delta_compact_m": delta[1] if delta else None,
                    "pre_press_m": pre[0] if pre else None,
                    "pre_sep_vel": pre[1] if pre else None,
                    "hold_s": hold.duration_s if hold else None,
                    "hold_exit": hold.exit if hold else None,
                }
            )
            kept += 1
        print(f"{m}: {kept} labeled")
    with open("data/pooled/idsse_retention_labeled.pkl", "wb") as f:
        pickle.dump(rows, f)
    print(f"banked {len(rows)} rows -> data/pooled/idsse_retention_labeled.pkl")


if __name__ == "__main__":
    main()
