"""Label retention touches on raw IDSSE tracking (gate 4, slice 3).

Reads the 7 raw matches, applies the slice-1 label rule at receipt+1 s,
banks (cushion, marking, controlled) rows. Slow (~2 min, 400 MB XML):
run on demand, not in CI. CI pins the banked file instead.
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
        prefix = f"/private/tmp/idsse_{m}" if m != "J03WPY" else "/private/tmp/idsse"
        length, width, teams, names = _load_roster(f"{prefix}_match.xml")
        frames, ball, stamps = _read_tracking(f"{prefix}_pos.xml", teams, length, width)
        passes = _read_passes(f"{prefix}_events.xml", stamps, teams, names)
        kept = 0
        for p in passes:
            found = _reception_point(ball, frames, p.start_frame, p.target_id)
            if found is None:
                continue
            end_pos, end_frame = found
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
            from src.models.retention.mechanism import label_touch

            rows.append(
                (
                    ready.post_cushion_s(res.margin_s),
                    w.marking_dist_m,
                    label_touch(w.ball_plus1, w.receiver_plus1),
                )
            )
            kept += 1
        print(f"{m}: {kept} labeled")
    with open("data/pooled/idsse_retention_labeled.pkl", "wb") as f:
        pickle.dump(rows, f)
    print(f"banked {len(rows)} rows -> data/pooled/idsse_retention_labeled.pkl")


if __name__ == "__main__":
    main()
