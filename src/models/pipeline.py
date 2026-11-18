"""Run one freeze through gates 3-4-5: arrival -> control -> loosen -> value.

The pipeline as a function, not a scripts folder. Takes a receiver,
opponent list, passer position, and reception latency; returns the
composition chain dataclasses. No loader I/O, no fitting — pure
composition of fitted gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from src.core.geometry import PitchPoint
from src.models.pressing.arrival import ArrivalResult, arrival_margin
from src.models.pressing.calibration import decile_risk, margin_decile
from src.models.pressing.readiness import ReadinessResult, receiver_readiness
from src.models.pressing.types import PressingActor
from src.models.retention.mechanism import (
    RetentionGivenArrival,
    loosen_given_control,
    retention_given_arrival,
)
from src.models.value_surface import outlet_value_fitted


@dataclass(frozen=True)
class OutletValue:
    margin_s: float
    cushion_s: float
    risk: Optional[float]
    control_prob: float
    loosen_prob: float
    value: float
    best_presser_id: Optional[int]
    marking_dist_m: float


def run_outlet(
    receiver: PressingActor,
    opponents: List[PressingActor],
    passer_pos: PitchPoint,
    pace_k: float = 1.0,
) -> OutletValue:
    """One outlet, gates 3-4-5 end to end.

    Arrival margin -> readiness cushion -> fitted control ->
    zone loosen -> value. Unscorable arrival (-99) propagates:
    risk None, control 0, loosen 0, value 0 — never a fitted number.
    """
    res: ArrivalResult = arrival_margin(receiver, opponents, passer_pos)
    if not res.margin_s > -99.0:
        return OutletValue(
            margin_s=res.margin_s,
            cushion_s=res.margin_s,
            risk=None,
            control_prob=0.0,
            loosen_prob=0.0,
            value=0.0,
            best_presser_id=None,
            marking_dist_m=99.0,
        )
    ready: ReadinessResult = receiver_readiness(receiver, passer_pos)
    comp: RetentionGivenArrival = retention_given_arrival(
        res, ready, res.marking_dist_m
    )
    zone = (
        "def"
        if receiver.pos_m.x < 35.0
        else ("mid" if receiver.pos_m.x < 70.0 else "att")
    )
    loosen = loosen_given_control(zone, True)
    dec = margin_decile(res.margin_s)
    return OutletValue(
        margin_s=res.margin_s,
        cushion_s=comp.cushion_s,
        risk=decile_risk(dec, pace_k),
        control_prob=comp.control_prob,
        loosen_prob=loosen,
        value=outlet_value_fitted(
            comp.control_prob, receiver.pos_m.x, loosen_prob=loosen
        ),
        best_presser_id=res.best_presser_id,
        marking_dist_m=res.marking_dist_m,
    )
