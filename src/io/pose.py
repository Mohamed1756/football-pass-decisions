"""SkillCorner 3D body-pose loader: joints to facing angle.

Pose frames (25 fps JSONL, plain or gzipped) carry 29 joints per
detected player with xyz meters plus p90_mae_cm per joint. This module
iterates frames and reduces shoulder geometry to a facing angle in the
same coordinate frame as the player x/y (joint centroid coincides with
tracked x/y on the sample phase, so no re-projection). Timestamp join
against 10 fps tracking belongs to the caller (pose_frame = 2.5 x
tracking_frame per the provider README); this module parses the
timestamp so both sides share seconds.
"""

from __future__ import annotations

import gzip
import json
import math
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, Optional, Tuple

# Worst-case single-joint angular error of 20 cm on a ~40 cm shoulder
# baseline is ~27 degrees, the validated EPTS orientation error budget
# cited in retention.md. Above it the open/needs-turn call is noise,
# so the joint is unusable and facing reads unknown (0.25 s floor
# downstream, provenance recorded — never a silently bad angle).
POSE_MAX_JOINT_ERR_CM: float = 20.0

# Joints that must be present and error-gated: the shoulder axis plus
# one forward reference to disambiguate the normal's sign.
SHOULDER_JOINTS: Tuple[str, ...] = ("lShoulder", "rShoulder", "midHip")


@dataclass(frozen=True)
class PoseFrame:
    frame: int
    timestamp_s: Optional[float]
    period: int
    joints: Dict[str, Optional[Dict[str, object]]]
    ball_xyz: Optional[Tuple[float, float, float]]


def _parse_timestamp(ts: object) -> Optional[float]:
    if not isinstance(ts, str) or not ts:
        return None
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600.0 + int(m) * 60.0 + float(s)
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60.0 + float(s)
    return None


def iter_pose_frames(path: str) -> Iterator[PoseFrame]:
    """Stream pose frames from .jsonl or .jsonl.gz, constant memory."""
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt") as f:
        yield from iter_pose_stream(f)


def iter_pose_stream(lines: Iterable[str]) -> Iterator[PoseFrame]:
    """Stream pose frames from an open text stream (incl. zip members)."""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        fr = json.loads(line)
        joints = {}
        for p in fr.get("player_data", []):
            joints[str(p["player_id"])] = p.get("joints")
        ball = fr.get("ball_data") or {}
        xyz = None
        if ball.get("x") is not None and ball.get("y") is not None:
            xyz = (
                float(ball["x"]),
                float(ball["y"]),
                float(ball.get("z", 0.0)),
            )
        yield PoseFrame(
            frame=int(fr["frame"]),
            timestamp_s=_parse_timestamp(fr.get("timestamp")),
            period=int(fr.get("period") or 0),
            joints=joints,
            ball_xyz=xyz,
        )


def _gated_xyz(
    joints: Dict[str, object], name: str
) -> Optional[Tuple[float, float, float]]:
    entry = joints.get(name)
    if not isinstance(entry, dict):
        return None
    xyz = entry.get("xyz")
    err = entry.get("p90_mae_cm")
    if (
        not isinstance(xyz, list)
        or len(xyz) != 3
        or not isinstance(err, (int, float))
        or err > POSE_MAX_JOINT_ERR_CM
    ):
        return None
    return (float(xyz[0]), float(xyz[1]), float(xyz[2]))


def facing_from_joints(joints: Dict[str, object]) -> Optional[float]:
    """Torso facing in radians, same frame as tracked x/y.

    Shoulder axis (right minus left) with the normal chosen toward the
    nose (neck fallback): the side of the axis the face is on is the
    facing side. Returns None when the axis, the forward reference, or
    any error gate fails — caller records unknown, never a bad angle.
    """
    left = _gated_xyz(joints, "lShoulder")
    right = _gated_xyz(joints, "rShoulder")
    mid = _gated_xyz(joints, "midHip")
    if left is None or right is None or mid is None:
        return None
    nose = _gated_xyz(joints, "nose") or _gated_xyz(joints, "neck")
    if nose is None:
        return None
    sx = right[0] - left[0]
    sy = right[1] - left[1]
    if sx == 0.0 and sy == 0.0:
        return None
    mx = (left[0] + right[0]) / 2.0
    my = (left[1] + right[1]) / 2.0
    fx, fy = nose[0] - mx, nose[1] - my
    # (−sy, sx) vs (sy, −sx): keep the normal the face is on.
    if fx * (-sy) + fy * sx >= fx * sy + fy * (-sx):
        nx, ny = -sy, sx
    else:
        nx, ny = sy, -sx
    if nx == 0.0 and ny == 0.0:
        return None
    return math.atan2(ny, nx)


def facing_source_tag() -> str:
    """Provenance string expected by resolve_facing for measured pose."""
    return "pose"
