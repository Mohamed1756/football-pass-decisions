"""Pose-facing bias check on 2 SkillCorner matches with 3D body pose.

For each ground pass with a measured reception (ball meets targeted
runner within 1 s, IDSSE rule ported to 10 fps), labels control at
receipt+1 s (1.5 m rule) and scores control probability twice with the
same fitted curve: once with all-unknown facing (0.25 s floors), once
with pose facing at the receipt frame (receiver + pressers, nearest
pose frame to 2.5x the tracking frame, tolerance 2). Reports the q1
fitted-vs-observed gap under both inputs. Read-only; prints only.
"""

import io
import math
import sys
import zipfile
from dataclasses import replace


sys.path.insert(0, ".")

from src.core.geometry import PitchPoint
from src.io.pose import facing_from_joints, iter_pose_stream
from src.io.skillcorner import (
    _load_match_meta,
    _read_passes,
    _velocity,
)
from src.models.pressing.arrival import (
    arrival_margin,
    presser_arrival_s,
    presser_engagement_latency_s,
)
from src.models.pressing.readiness import receiver_readiness
from src.models.pressing.types import PressingActor, gate_tracking_velocity
from src.models.retention.mechanism import fitted_control_prob, label_touch

MATCHES = [1925299, 1996435]
TRACKING = {1925299: "/tmp/tr1925299.jsonl", 1996435: "/tmp/tr1996435.jsonl"}


def _read_tracking_f(path, length, width):
    """Tracking restricted to detected players; extrapolated ghosts dropped.

    Diagnostic-strict: the shared loader keeps ghosts (banked pools depend
    on that mapping). Ghost velocities and phantom marking corrupt both
    cushions and the touch label, so this diagnostic filters them here.
    """
    import json as _json

    frames = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            fr = _json.loads(line)
            players = {}
            for p in fr.get("player_data", []):
                if p.get("player_id") is None or p.get("x") is None:
                    continue
                if p.get("is_detected") is False:
                    continue
                players[str(p["player_id"])] = (
                    float(p["x"]) + length / 2.0,
                    float(p["y"]) + width / 2.0,
                )
            frames[int(fr["frame"])] = players
    return frames


def _read_ball_f(path, length, width):
    """Ball track restricted to detected frames; see _read_tracking_f."""
    import json as _json

    out = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            fr = _json.loads(line)
            bd = fr.get("ball_data") or {}
            if bd.get("x") is None or bd.get("is_detected") is False:
                continue
            out[int(fr["frame"])] = (
                float(bd["x"]) + length / 2.0,
                float(bd["y"]) + width / 2.0,
            )
    return out


EVENTS = {
    1925299: "/tmp/sc_meta/1925299_events.csv",
    1996435: "/tmp/sc_meta/1996435_events.csv",
}
MATCHMETA = {
    1925299: "/tmp/sc_meta/1925299_match.json",
    1996435: "/tmp/sc_meta/1996435_match.json",
}
POSEZIP = {
    1925299: "/tmp/skillcorner_pose/raw/1925299.jsonl.zip",
    1996435: "/tmp/skillcorner_pose/raw/1996435.jsonl.zip",
}
POSE_TOL_FRAMES: int = 2

# Event frames lag tracking frames by a constant 20 (grid-searched
# minimum, stable across periods: ball-target p50 2.0 m at +20 vs
# 13.6 m at +0 on match 1925299). Applied to every tracking/ball
# lookup keyed by an event frame. Local to this diagnostic; the shared
# loader is untouched (banked pools depend on its mapping).
EVENT_FRAME_OFFSET: int = 20
# Receipt verification gate: ball within this of the target at the
# annotated end frame. Generous vs the IDSSE 2 m rule — 10 fps
# broadcast extrapolation, not 25 fps optical. Rows failing it are
# dropped and counted, never silently kept.
RECEIPT_VERIFY_M: float = 5.0


def main() -> None:
    rows = []
    cov = {"recv_resolved": 0, "recv_total": 0, "press_resolved": 0, "press_total": 0}
    for m in MATCHES:
        length, width, teams = _load_match_meta(MATCHMETA[m])
        frames = _read_tracking_f(TRACKING[m], length, width)
        ball = _read_ball_f(TRACKING[m], length, width)
        passes = _read_passes(EVENTS[m], length, width)
        z = zipfile.ZipFile(POSEZIP[m])
        (member,) = [
            n for n in z.namelist() if n.endswith(".jsonl") and "__MACOSX" not in n
        ]
        pose_by_frame = {}
        with z.open(member) as f:
            for fr in iter_pose_stream(io.TextIOWrapper(f)):
                pose_by_frame[fr.frame] = fr
        kept = 0
        unverified = 0
        for p in passes:
            # Receipt anchored at the annotated end frame (broadcast
            # flights exceed the 1 s IDSSE window: median 12 frames),
            # verified — not discovered — against the ball track.
            end_frame = p.end_frame + EVENT_FRAME_OFFSET
            start_frame = p.start_frame + EVENT_FRAME_OFFSET
            b_end = ball.get(end_frame)
            r_end = frames.get(end_frame, {}).get(p.target_id)
            if b_end is None or r_end is None:
                continue
            end_pos = PitchPoint(*b_end)
            if math.dist(b_end, r_end) > RECEIPT_VERIFY_M:
                unverified += 1
                continue
            w_ball = ball.get(end_frame + 10)
            w_recv = frames.get(end_frame + 10, {}).get(p.target_id)
            if w_ball is None or w_recv is None:
                continue
            controlled = label_touch(PitchPoint(*w_ball), PitchPoint(*w_recv))
            side = teams.get(p.target_id)
            f0 = frames.get(start_frame, {})
            mates = {pid: pos for pid, pos in f0.items() if teams.get(pid) == side}
            opps = {pid: pos for pid, pos in f0.items() if teams.get(pid) != side}
            if p.target_id not in mates or not opps:
                continue
            # Receiver + live pressers at the pass frame (IDSSE pattern).
            rec_vel = _velocity(frames, start_frame, p.target_id)
            rec = PressingActor(
                track_id=0,
                team_id=side or "unknown",
                pos_m=PitchPoint(*mates[p.target_id]),
                vel_ms=rec_vel,
                provider_id=p.target_id,
            )
            opp_actors = []
            for tid, (pid, pos) in enumerate(sorted(opps.items())):
                vel = _velocity(frames, start_frame, pid)
                opp_actors.append(
                    PressingActor(
                        track_id=tid,
                        team_id="opp",
                        pos_m=PitchPoint(*pos),
                        vel_ms=vel,
                        provider_id=pid,
                    )
                )
            t_ball = (end_frame - start_frame) / 10.0
            res = arrival_margin(
                rec,
                opp_actors,
                p.passer_pos_m,
                live_pressers=True,
                measured=(end_pos, t_ball),
            )
            if res.margin_s <= -99.0 or res.intercept_m is None:
                continue
            ready = receiver_readiness(rec, p.passer_pos_m)
            cushion_floor = ready.post_cushion_s(res.margin_s)

            # Pose facing at the receipt frame (start of both races).
            pf = pose_by_frame.get(round(2.5 * end_frame))
            if pf is None:
                pf = min(
                    pose_by_frame.values(),
                    key=lambda fr: abs(fr.frame - 2.5 * end_frame),
                    default=None,
                )
                if pf is None or abs(pf.frame - 2.5 * end_frame) > POSE_TOL_FRAMES:
                    pf = None
            facing = {}
            if pf is not None:
                for pid, js in pf.joints.items():
                    if js is not None:
                        a = facing_from_joints(js)
                        if a is not None:
                            facing[pid] = a
            cov["recv_total"] += 1
            recv_face = facing.get(p.target_id)
            if recv_face is not None:
                cov["recv_resolved"] += 1
            press_face = {}
            for op in opp_actors:
                cov["press_total"] += 1
                if op.provider_id in facing:
                    cov["press_resolved"] += 1
                    press_face[op.provider_id] = facing[op.provider_id]

            # Pose-input cushion: receiver turn priced off pose facing.

            rec_pose = (
                replace(rec, facing_rad=recv_face, facing_source="pose")
                if recv_face is not None
                else rec
            )
            ready_pose = receiver_readiness(rec_pose, p.passer_pos_m)
            cushion_pose = ready_pose.post_cushion_s(res.margin_s)

            # Pose-input press: engagement latencies off pose facing.
            t_press_pose = math.inf
            for op in opp_actors:
                face = press_face.get(op.provider_id)
                o = (
                    replace(op, facing_rad=face, facing_source="pose")
                    if face is not None
                    else op
                )
                (vx, vy), _ = gate_tracking_velocity(o.vel_ms, o.speed_capped)
                adv = replace(
                    o,
                    pos_m=PitchPoint(o.pos_m.x + vx * t_ball, o.pos_m.y + vy * t_ball),
                )
                eng, _ = presser_engagement_latency_s(adv, res.intercept_m)
                arr, _ = presser_arrival_s(
                    adv, res.intercept_m, engagement_latency_s=eng
                )
                t_press_pose = min(t_press_pose, arr)
            margin_pose = (
                round(t_press_pose - t_ball, 3)
                if math.isfinite(t_press_pose)
                else -99.0
            )
            cushion_pose_press = (
                ready_pose.post_cushion_s(margin_pose)
                if margin_pose > -99.0
                else margin_pose
            )
            rows.append(
                {
                    "match": m,
                    "controlled": controlled,
                    "cushion_floor": cushion_floor,
                    "cushion_pose": cushion_pose,
                    "cushion_pose_press": cushion_pose_press,
                }
            )
            kept += 1
        print(f"{m}: {kept} labeled receptions ({unverified} unverified)")
    print("coverage:", cov)
    print(f"n={len(rows)}")
    import statistics

    obs = sum(1 for r in rows if r["controlled"]) / len(rows)
    print(f"observed control={obs:.3f}")
    for key in ("cushion_floor", "cushion_pose", "cushion_pose_press"):
        cs = sorted(r[key] for r in rows if r[key] > -99.0)
        print(
            f"{key}: med={statistics.median(cs):+.2f} "
            f"q1max={cs[len(cs) // 10]:+.2f} min={cs[0]:+.2f}"
        )
        # Ordering check: AUC of cushion vs control label. Levels are
        # out-of-scale on measured broadcast inputs (curve fit on IDSSE
        # short-pass cushions, min -1.028); rank is the portable claim.
        pos = sorted((r[key], r["controlled"]) for r in rows if r[key] > -99.0)
        rank_of = {}
        for i, (v, _) in enumerate(pos):
            rank_of.setdefault(v, []).append(i + 1)
        auc_num = 0.0
        n1 = sum(1 for _, c in pos if c)
        for v, c in pos:
            if c:
                auc_num += sum(rank_of[v]) / len(rank_of[v])
        auc = (auc_num - n1 * (n1 + 1) / 2) / (n1 * (len(pos) - n1))
        print(f"{key}: AUC={auc:.3f}")
        q = [cs[int(len(cs) * i / 10)] for i in range(1, 10)]
        q1 = [r for r in rows if not any(r[key] > e for e in q)]
        pred = sum(fitted_control_prob(r[key]) for r in q1) / len(q1)
        act = sum(1 for r in q1 if r["controlled"]) / len(q1)
        print(f"{key}: q1 n={len(q1)} fitted={pred:.3f} observed={act:.3f}")


if __name__ == "__main__":
    main()
