"""Formation window: press access and separation velocity at the freeze.

Gate 0 descriptors that move: nearest-opponent distance to ball (state)
and its rate of change over [-5 s, 0] (derivative). Open-man counts cut:
repositioning without separation (+0.01 to +0.21 everywhere) — noise
with a name. See gate5.md for the same cut on the resolution side.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class FormationWindow:
    press_access_at_freeze_m: float
    separation_velocity_ms: float


def _nearest_opp_dist(
    pos: Tuple[float, float], opponents: List[Tuple[float, float]]
) -> float:
    return min(math.dist(pos, o) for o in opponents) if opponents else math.inf


def formation_window(
    ball_at_freeze: Tuple[float, float],
    teammates_at_freeze: Dict[str, Tuple[float, float]],
    opponents_at_freeze: Dict[str, Tuple[float, float]],
    teammate_tracks: Dict[str, List[Tuple[float, float]]],
) -> FormationWindow:
    """Pre-freeze shape from tracking ending at the pass event.

    teammate_tracks maps each teammate to its positions over [-5 s, 0],
    oldest first, same frame rate throughout. Separation velocity is the
    mean per-teammate rate of change of nearest-opponent distance over
    the window, opponents frozen at t=0 for both endpoints: teammate
    motion relative to the final shape, not separation dynamics —
    positive = men getting opener into the freeze, under the same
    frozen-snapshot convention as the rest of the instrument.
    teammates_at_freeze kept for signature stability; the resolution
    side needs no per-teammate positions once counts are cut.
    Missing tracks (untracked at any window frame) are skipped, same
    reception-conditioning as gates 4-5.
    """
    _ = teammates_at_freeze
    opps = list(opponents_at_freeze.values())
    press = _nearest_opp_dist(ball_at_freeze, opps)
    vels = []
    for pid, track in teammate_tracks.items():
        if len(track) < 2 or not opps:
            continue
        d0 = _nearest_opp_dist(track[0], list(opponents_at_freeze.values()))
        d1 = _nearest_opp_dist(track[-1], list(opponents_at_freeze.values()))
        dt = len(track) - 1
        if math.isfinite(d0) and math.isfinite(d1) and dt > 0:
            vels.append((d1 - d0) / dt)
    sep_vel = sum(vels) / len(vels) if vels else 0.0
    return FormationWindow(
        press_access_at_freeze_m=round(press, 2),
        separation_velocity_ms=round(sep_vel, 3),
    )


def freeze_given_delta() -> None:
    """Gate 5 → gate 0 composition: previous press-delta carries no usable
    information about next openness (unfiltered Pearson +0.10 on 1,152
    linked pairs, Spearman +0.05; +0.02 on the 655 previous-controlled
    pairs, pinned in test_formation_transition).

    Returns None by design, not by omission: the loop is architecture,
    not evidence. Callers wanting next-freeze description use
    formation_window directly; callers wanting prediction look
    elsewhere. This stub exists so the composition slot is closed,
    not open.
    """
    return None
