"""Structure-delta mechanism: how the freeze resolved.

Two components that move: press access and compactness, after minus
before. Open-man counts cut: +0.01 to +0.21 everywhere — repositioning
without separation, noise with a name. See freeze.md for the same cut
on the formation side.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class StructureDelta:
    press_access_delta_m: float
    compactness_delta_m: float


def _nearest_opp_dist(
    pos: Tuple[float, float], opponents: List[Tuple[float, float]]
) -> float:
    return min(math.dist(pos, o) for o in opponents) if opponents else math.inf


def structure_delta(
    ball_before: Tuple[float, float],
    ball_after: Tuple[float, float],
    teammates_before: Dict[str, Tuple[float, float]],
    teammates_after: Dict[str, Tuple[float, float]],
    opponents_before: Dict[str, Tuple[float, float]],
    opponents_after: Dict[str, Tuple[float, float]],
) -> StructureDelta:
    """Before/after frame arithmetic. Positive = structure loosened.

    Press access: nearest-opponent distance to ball, after minus
    before. Compactness: mean opponent distance to ball, after minus
    before. Teammate dicts kept for signature stability; the count
    is gone. Missing actors (untracked at either freeze) are skipped,
    not zeroed — same reception-conditioning as gate 4.
    """
    _ = (teammates_before, teammates_after)
    opp_b = list(opponents_before.values())
    opp_a = list(opponents_after.values())
    press = _nearest_opp_dist(ball_after, opp_a) - _nearest_opp_dist(ball_before, opp_b)

    def compactness(
        ball: Tuple[float, float], opps: List[Tuple[float, float]]
    ) -> float:
        return sum(math.dist(ball, o) for o in opps) / len(opps) if opps else 0.0

    comp = compactness(ball_after, opp_a) - compactness(ball_before, opp_b)
    return StructureDelta(
        press_access_delta_m=round(press, 2),
        compactness_delta_m=round(comp, 2),
    )
