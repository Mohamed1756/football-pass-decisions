"""Retention mechanism: control given arrival, fitted on 1,160 labels.

Single home for the winner curve (fitted_control_prob), the gate-3→4
composition (retention_given_arrival), the gate-4→5 loosen map
(loosen_given_control), and the touch label rule.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from src.core.geometry import PitchPoint
from src.models.pressing.arrival import ArrivalResult
from src.models.pressing.readiness import ReadinessResult

# Deleted as unverifiable (fit voted direct curve, NLL 782.6):
# touch_need_s, disrupt_time_s, RetentionMargin, retention_margin_s —
# the race machinery the composition bypasses. Cut, not kept: the
# sketch's deleted-alternatives list owns them now.


# Touch-label rule: ball within this radius of the receiver at
# receipt+1 s counts as controlled. Cited, not tuned: 2 m reception
# radius (IDSSE loader) tightened for control — still a ball at feet,
# not a ball nearby.
CONTROL_RADIUS_M: float = 1.5


@dataclass(frozen=True)
class RetentionGivenArrival:
    margin_s: float
    cushion_s: float
    marking_dist_m: float
    control_prob: float


def retention_given_arrival(
    arrival: ArrivalResult,
    readiness: ReadinessResult,
    marking_dist_m: float,
) -> RetentionGivenArrival:
    """Gate 3 → gate 4: arrival outputs in, control probability out.

    Takes the dataclasses, not floats: cushion comes from
    readiness.post_cushion_s (single subtraction, single owner).
    Unscorable arrival (-99) stays unscorable: the fit never sees it,
    control reads 0.0, never a fitted value. Control follows the
    winner curve (fitted_control_prob); params live there, not here.
    """
    if arrival.margin_s <= -99.0:
        return RetentionGivenArrival(
            margin_s=arrival.margin_s,
            cushion_s=arrival.margin_s,
            marking_dist_m=marking_dist_m,
            control_prob=0.0,
        )
    cushion = readiness.post_cushion_s(arrival.margin_s)
    return RetentionGivenArrival(
        margin_s=arrival.margin_s,
        cushion_s=cushion,
        marking_dist_m=marking_dist_m,
        control_prob=fitted_control_prob(cushion),
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


def touch_curve_exp(cushion_s: float, lam: float = 0.40, c0: float = -1.50) -> float:
    """Shifted exponential: P = 1 - e^(-lam (t - c0)), floored at 0 below c0.

    Defaults are the winner (pinned in test_retention_fit); pass
    lam=4.3, c0=0.0 for the Spearman 2017 EPL form as challenger.
    """
    if cushion_s <= c0:
        return 0.0
    return round(1.0 - math.exp(-lam * (cushion_s - c0)), 4)


# Winner constants (pinned in test_retention_fit on 1,160 labeled rows).
FIT_LAM: float = 0.40
FIT_C0: float = -1.50


def fitted_control_prob(cushion_s: float) -> float:
    """Winner curve. Single home: tests import this, never redefine."""
    return touch_curve_exp(cushion_s, FIT_LAM, FIT_C0)


# P(pass loosens structure | controlled, reception zone): press access
# > 0 rate on banked controlled receptions (180/316/163 per zone).
# Pinned in test_structure_fit. Uncontrolled rows excluded by definition
# (gate 5's estimand conditions on control); no-control callers get 0.0.
LOOSEN_RATE_BY_ZONE = {"def": 0.356, "mid": 0.351, "att": 0.258}


def loosen_given_control(zone: str, controlled: bool) -> float:
    """Gate 4 → gate 5: control + zone in, loosen probability out.

    Single home for the zone table: value_surface calls this instead
    of taking a caller-supplied map. Unknown zones and uncontrolled
    receptions read 0.0 — never a fitted value.
    """
    if not controlled:
        return 0.0
    return LOOSEN_RATE_BY_ZONE.get(zone, 0.0)
