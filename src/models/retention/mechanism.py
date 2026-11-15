"""Retention mechanism: touch_need vs t_disrupt, clocked from reception.

Gate 4 slice 1: pure functions on synthetic values only. No loader
changes, no fit, no banked pools. The touch label rule lives here so
slice 3 applies it unchanged to the 1,160 measured receptions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from src.core.geometry import PitchPoint

# Placeholder population mean: uniform-over-angles expected turn on the
# hip-pivot curve (0.39 s, computed not asserted). ASSUMED until pose
# data replaces it. Floor 0 rejected: prices ignorance as ideal
# preparation.
UNKNOWN_FACING_TURN_S: float = 0.39

# Touch-label rule: ball within this radius of the receiver at
# receipt+1 s counts as controlled. Cited, not tuned: 2 m reception
# radius (IDSSE loader) tightened for control — still a ball at feet,
# not a ball nearby.
CONTROL_RADIUS_M: float = 1.5


def touch_need_s(turn_latency_s: float, facing_known: bool) -> float:
    """Seconds to control: 0.45 s touch plus turn cost.

    Unknown facing takes the placeholder mean, not floor 0 (see module
    docstring). The 0.25 s engagement floor stays on the presser's
    clock — charged once, upstream.
    """
    from src.physics.arrival_constants import RECEIVER_FIRST_TOUCH_LATENCY_S

    turn = turn_latency_s if facing_known else UNKNOWN_FACING_TURN_S
    return round(RECEIVER_FIRST_TOUCH_LATENCY_S + turn, 3)


def disrupt_time_s(marking_dist_m: float, closing_speed_ms: float) -> float:
    """Presser seconds to contest: distance over closing speed.

    Sprint-cap fallback when no velocity: callers pass
    PRESSER_SPRINT_MAX_SPEED_MS instead of zero so stationary tracking
    reads as worst-case close, not infinite time.
    """
    if closing_speed_ms <= 0.0:
        return math.inf
    return round(marking_dist_m / closing_speed_ms, 3)


@dataclass(frozen=True)
class RetentionMargin:
    touch_need_s: float
    t_disrupt_s: float
    margin_s: float


def retention_margin_s(touch_need: float, t_disrupt: float) -> RetentionMargin:
    """Second race, same shape as arrival: control holds iff margin > 0."""
    return RetentionMargin(
        touch_need_s=touch_need,
        t_disrupt_s=t_disrupt,
        margin_s=round(t_disrupt - touch_need, 3),
    )


def label_touch(ball_plus1: PitchPoint, receiver_plus1: PitchPoint) -> bool:
    """Controlled iff ball within CONTROL_RADIUS_M at receipt+1 s.

    Binary by design: nothing in tracking + events draws a
    controlled/contested boundary with a rule.
    """
    return (
        math.dist((ball_plus1.x, ball_plus1.y), (receiver_plus1.x, receiver_plus1.y))
        <= CONTROL_RADIUS_M
    )


def touch_curve_logistic(cushion_s: float, steepness: float, midpoint: float) -> float:
    """Logistic touch curve. Params as args: contest harness, not a pick.

    Current assumed values (steepness 15, midpoint 0.15) are the null
    to beat, not constants — see retention.md.
    """
    return round(1.0 / (1.0 + math.exp(-steepness * (cushion_s - midpoint))), 4)


def touch_curve_exp(cushion_s: float, lam: float) -> float:
    """Exponential touch curve: P = 1 - e^(-lam t). Spearman 2017 form.

    Params as args, same contest. Spearman fit lam = 4.3/s on EPL.
    """
    return round(1.0 - math.exp(-lam * cushion_s), 4)
