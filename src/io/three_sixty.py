"""StatsBomb 360 loader: freeze frames + pass events to canonical outlets.

360 snapshots join events by event_uuid. Coordinates are 120x80 vendor
units, mapped linear to canonical 105x68 meters on read (same edge as
the IDSSE center-origin shift). Choice set = in-frame teammates minus
the actor (passer-self); freeze frames carry no identities, so the
chosen outlet is the nearest teammate to the pass end location, with
the distance banked as the misattribution audit trail. Ground passes
only (Height == Ground Pass), matching the frozen-fit conditioning.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from src.core.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M

SB_W: float = 120.0
SB_H: float = 80.0

# Passer-self exclusion needs no lookup: the frame flags the actor.
# Chosen-outlet mapping is nearest-to-end by construction (no identity
# in the frame); distances above this are counted, never silently kept.
RECIPIENT_VERIFY_M: float = 5.0


@dataclass(frozen=True)
class FrozenOutlet:
    """One in-frame player: canonical position + role flags."""

    pos_m: Tuple[float, float]
    is_actor: bool
    is_keeper: bool
    is_mate: bool = True


@dataclass(frozen=True)
class SBPass:
    event_uuid: str
    passer_team: str
    target_name: str
    timestamp_s: float
    passer_pos_m: Tuple[float, float]
    end_pos_m: Tuple[float, float]
    complete: bool
    period: int


def _parse_timestamp(ts: object) -> float:
    if not isinstance(ts, str) or not ts:
        return 0.0
    parts = ts.split(":")
    try:
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600.0 + int(m) * 60.0 + float(s)
        if len(parts) == 2:
            m, s = parts
            return int(m) * 60.0 + float(s)
    except ValueError:
        return 0.0
    return 0.0


def _to_canonical(x: float, y: float) -> Tuple[float, float]:
    return (x / SB_W * PITCH_LENGTH_M, y / SB_H * PITCH_WIDTH_M)


def _read_freeze(path: str) -> Dict[str, List[FrozenOutlet]]:
    """event_uuid -> in-frame players (mates flagged; actor = passer)."""
    with open(path) as f:
        frames = json.load(f)
    out: Dict[str, List[FrozenOutlet]] = {}
    for fr in frames:
        mates = []
        for p in fr.get("freeze_frame", []):
            loc = p.get("location") or [None, None]
            if loc[0] is None or loc[1] is None:
                continue
            mates.append(
                FrozenOutlet(
                    pos_m=_to_canonical(float(loc[0]), float(loc[1])),
                    is_actor=bool(p.get("actor")),
                    is_keeper=bool(p.get("keeper")),
                    is_mate=bool(p.get("teammate")),
                )
            )
        out[str(fr.get("event_uuid"))] = mates
    return out


def _read_passes(path: str) -> List[SBPass]:
    """Ground passes with a named recipient and an outcome."""
    with open(path) as f:
        events = json.load(f)
    out: List[SBPass] = []
    for e in events:
        if not isinstance(e, dict) or e.get("type", {}).get("name") != "Pass":
            continue
        pb = e.get("pass", {})
        if not isinstance(pb, dict) or not pb.get("recipient"):
            continue
        if pb.get("height", {}).get("name", "Ground Pass") != "Ground Pass":
            continue
        outcome = pb.get("outcome", {}).get("name", "Successful")
        if outcome not in ("Successful", "Unsuccessful"):
            continue
        loc = e.get("location") or [None, None]
        end = pb.get("end_location") or [None, None]
        if None in loc or None in end:
            continue
        sx, sy = _to_canonical(float(loc[0]), float(loc[1]))
        ex, ey = _to_canonical(float(end[0]), float(end[1]))
        out.append(
            SBPass(
                event_uuid=str(e.get("id")),
                passer_team=str(e.get("team", {}).get("name", "unknown")),
                target_name=str(pb["recipient"].get("name", "")),
                timestamp_s=_parse_timestamp(e.get("timestamp")),
                passer_pos_m=(sx, sy),
                end_pos_m=(ex, ey),
                complete=outcome == "Successful",
                period=int(e.get("period", 0) or 0),
            )
        )
    return out


def choose_outlet(
    mates: List[FrozenOutlet], end_pos_m: Tuple[float, float]
) -> Tuple[Optional[int], float]:
    """Nearest non-actor teammate to the pass end point + distance.

    Returns (index, distance); index None when no teammate is usable.
    Passer-self (actor) never counts as an outlet.
    """
    best: Optional[int] = None
    best_d = math.inf
    for i, m in enumerate(mates):
        if m.is_actor or not m.is_mate:
            continue
        d = math.dist(m.pos_m, end_pos_m)
        if d < best_d:
            best, best_d = i, d
    if best is None:
        return None, math.inf
    return best, round(best_d, 2)
