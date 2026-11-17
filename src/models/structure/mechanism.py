"""Structure-delta mechanism: how the freeze resolved.

Gate 5 slice 1: pure frame arithmetic on hand slices only. No loader
changes, no fit, no banked deltas. The three components live here so
slice 3 applies them unchanged to the 1,160 measured receptions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

# Open-man threshold: median marking distance on 1,160 banked
# receptions is 5.64 m; 5 m splits tight (<50% control) from loose
# (>65% control) coverage. Cited from the pool, not tuned.
OPEN_MAN_RADIUS_M: float = 5.0


@dataclass(frozen=True)
class StructureDelta:
    press_access_delta_m: float
    open_men_delta: int
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
    before. Open men: teammates with separation > OPEN_MAN_RADIUS_M
    from their nearest opponent, after minus before. Compactness:
    mean opponent distance to ball, after minus before.
    Missing actors (untracked at either freeze) are skipped, not
    zeroed — same reception-conditioning as gate 4.
    """
    opp_b = list(opponents_before.values())
    opp_a = list(opponents_after.values())
    press = _nearest_opp_dist(ball_after, opp_a) - _nearest_opp_dist(ball_before, opp_b)

    def open_men(
        mates: Dict[str, Tuple[float, float]], opps: Dict[str, Tuple[float, float]]
    ) -> int:
        n = 0
        for pos in mates.values():
            if not opps:
                continue
            if _nearest_opp_dist(pos, list(opps.values())) > OPEN_MAN_RADIUS_M:
                n += 1
        return n

    men = open_men(teammates_after, opponents_after) - open_men(
        teammates_before, opponents_before
    )

    def compactness(
        ball: Tuple[float, float], opps: List[Tuple[float, float]]
    ) -> float:
        return sum(math.dist(ball, o) for o in opps) / len(opps) if opps else 0.0

    comp = compactness(ball_after, opp_a) - compactness(ball_before, opp_b)
    return StructureDelta(
        press_access_delta_m=round(press, 2),
        open_men_delta=men,
        compactness_delta_m=round(comp, 2),
    )
