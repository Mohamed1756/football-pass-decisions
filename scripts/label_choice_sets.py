"""Bank per-freeze full choice sets on IDSSE tracking.

Raw prerequisite: the 7 matches at /tmp/idsse_raw (HuggingFace
`pysport/idsse-data`, re-downloadable). For each ground pass with an
observed reception (same conditioning as label_retention.py), scores
every tracked teammate as an outlet at the pass frame with frozen
arrival margins, ranks the chosen target with rank_outlets, and
summarizes the set with affordance_volume. Slow (~2 min, 400 MB
XML): run on demand, not in CI. CI pins the banked file instead.

Passer exclusion: the event names the passer by short name, not
PersonId. Reverse lookup (name + team) uniquely identifies the
passer pid in the common case; that pid leaves the outlet set.
On ambiguous or missing lookup the nearest mate to the ball fills
in; the per-match fallback count is printed, never hidden.
Frozen margins match the calibration convention (360 snapshots
carry no velocities); the loader-measured speeds stay out.
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
)
from src.models.formation.mechanism import affordance_volume
from src.models.pressing.arrival import arrival_margin
from src.models.pressing.calibration import rank_outlets
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
        rev = {}
        for pid, nm in names.items():
            rev.setdefault((nm, teams.get(pid)), []).append(pid)
        kept = 0
        fallback = 0
        degenerate = 0
        for p in passes:
            if _reception_point(ball, frames, p.start_frame, p.target_id) is None:
                continue
            f0 = p.start_frame
            frame = frames.get(f0)
            b0 = ball.get(f0)
            if not frame or b0 is None:
                continue
            side = teams.get(p.target_id)
            mates = {pid: pos for pid, pos in frame.items() if teams.get(pid) == side}
            opps = {pid: pos for pid, pos in frame.items() if teams.get(pid) != side}
            if not mates or not opps or p.target_id not in mates:
                continue
            cands = rev.get((p.passer, p.passer_team), [])
            is_fallback = False
            if len(cands) == 1 and cands[0] in mates and cands[0] != p.target_id:
                mates.pop(cands[0])
            else:
                # Unique lookup that misses the pitch is a miss, not an
                # exclusion: pop() with a default would silently keep the
                # passer-self outlet. Fallback never takes the target (a
                # receiver is never his own passer); with no other mate
                # the row is degenerate and dropped, counted below.
                is_fallback = True
                fallback += 1
                others = [pid for pid in mates if pid != p.target_id]
                if not others:
                    degenerate += 1
                    continue
                nearest = min(
                    others,
                    key=lambda pid: (mates[pid][0] - b0[0]) ** 2
                    + (mates[pid][1] - b0[1]) ** 2,
                )
                mates.pop(nearest, None)
            if p.target_id not in mates or not mates:
                continue
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
            outlet_pids = sorted(mates)
            margins = []
            for tid, pid in enumerate(outlet_pids):
                pos = mates[pid]
                res = arrival_margin(
                    PressingActor(
                        track_id=tid,
                        team_id=side or "unknown",
                        pos_m=PitchPoint(*pos),
                        provider_id=pid,
                    ),
                    opp_actors,
                    passer_pos,
                )
                margins.append(res.margin_s)
            ranks = rank_outlets(margins)
            chosen_rank = ranks[outlet_pids.index(p.target_id)].rank
            av = affordance_volume(margins)
            rows.append(
                {
                    "match": m,
                    "pass_idx": p.start_frame,
                    "target_id": p.target_id,
                    "complete": p.complete,
                    "n_outlets": len(outlet_pids),
                    "n_viable": av.n_viable,
                    "entropy_bits": av.entropy_bits,
                    "effective_options": av.effective_options,
                    "chosen_rank": chosen_rank,
                    "chosen_margin": margins[outlet_pids.index(p.target_id)],
                    "margins": margins,
                    "outlet_pids": outlet_pids,
                    "passer_fallback": is_fallback,
                }
            )
            kept += 1
        print(f"{m}: {kept} sets ({fallback} fallbacks, {degenerate} degenerate)")
    with open("data/pooled/idsse_choice_sets_labeled.pkl", "wb") as f:
        pickle.dump(rows, f)
    print(f"banked {len(rows)} sets -> data/pooled/idsse_choice_sets_labeled.pkl")


if __name__ == "__main__":
    main()
