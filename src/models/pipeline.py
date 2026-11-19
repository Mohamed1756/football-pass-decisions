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
    loosen_prob_given_control: float
    value: float
    best_presser_id: Optional[int]
    marking_dist_m: float


def run_outlet(
    receiver: PressingActor,
    opponents: List[PressingActor],
    passer_pos: PitchPoint,
    pace_k: float = 1.0,
    source: str = "frozen",
) -> OutletValue:
    """One outlet, gates 3-4-5 end to end.

    Arrival margin -> readiness cushion -> fitted control ->
    zone loosen -> value. value = control x progress x loosen is the
    conditional factorization of sticking and loosening given arrival
    (progress is a deterministic weight, not a random variable).
    loosen_prob_given_control is conditional: the joint loosening is
    control x loosen (at control 0.05 and loosen 0.35, joint 0.018).
    Unscorable arrival (-99) propagates:
    risk None, control 0, loosen 0, value 0 — never a fitted number.

    source refuses ordering-only inputs: "frozen" (360 snapshots)
    raises ValueError — rank outlets with rank_outlets and bin with
    margin_decile instead of scoring levels here. What the flag does
    not do is validate scale. Scoring stays frozen-model regardless:
    arrival runs the frozen flight estimator (no measured flight, no
    live pressers), so control_prob on a frozen cushion is
    ordering-only — calibrated IDSSE levels need measured flight
    (reconciliation is Q8 work, not this flag). source="tracking"
    means the caller asserts non-360 inputs, not that the computation
    honors their scale.
    """
    if source not in ("tracking", "frozen"):
        raise ValueError(f"source must be 'tracking' or 'frozen', got {source!r}")
    if source == "frozen":
        raise ValueError(
            "run_outlet scores fitted levels (control curve, decile edges); "
            "frozen 360 snapshots carry ordering only. See retention.md."
        )
    res: ArrivalResult = arrival_margin(receiver, opponents, passer_pos)
    if not res.margin_s > -99.0:
        return OutletValue(
            margin_s=res.margin_s,
            cushion_s=res.margin_s,
            risk=None,
            control_prob=0.0,
            loosen_prob_given_control=0.0,
            value=0.0,
            best_presser_id=None,
            marking_dist_m=99.0,
        )
    ready: ReadinessResult = receiver_readiness(receiver, passer_pos)
    comp: RetentionGivenArrival = retention_given_arrival(
        res, ready, res.marking_dist_m
    )
    # Reception-keyed covariates: the fitted zone rates key on recept_x_m
    # and progress on the intercept, not the freeze position. A receiver
    # crossing 35/70 m between freeze and reception otherwise takes the
    # wrong zone rate and progress.
    assert res.intercept_m is not None  # scored path has an intercept
    zone = (
        "def"
        if res.intercept_m.x < 35.0
        else ("mid" if res.intercept_m.x < 70.0 else "att")
    )
    loosen = loosen_given_control(zone, True)
    dec = margin_decile(res.margin_s)
    return OutletValue(
        margin_s=res.margin_s,
        cushion_s=comp.cushion_s,
        risk=decile_risk(dec, pace_k),
        control_prob=comp.control_prob,
        loosen_prob_given_control=loosen,
        value=outlet_value_fitted(
            comp.control_prob, res.intercept_m.x, loosen_prob=loosen
        ),
        best_presser_id=res.best_presser_id,
        marking_dist_m=res.marking_dist_m,
    )
