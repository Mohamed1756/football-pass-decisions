"""Value surface: fitted control x forward progress per pitch cell.

Gate 3 x gate 4 rendered as a surface. Same grid loop as risk_surface,
but per cell the composition runs arrival -> readiness -> fitted
control curve, and value multiplies control by forward progress (same
progress term as the old outlet_value, cut with the assumed curve).
scored: the bivariate discount buys dNLL 1.2 on 1,160 rows — real but
small, and wiring it now would pretend a fitted joint form exists.
Revisit when the marking term earns its parameters.

Unscorable cells (no valid presser) carry risk=None, control 0.0,
value 0.0: never displayed as safe or valuable.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import List, Optional

from src.core.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, PitchPoint
from src.models.pressing.arrival import arrival_margin
from src.models.pressing.calibration import decile_risk, margin_decile
from src.models.pressing.readiness import receiver_readiness
from src.models.pressing.types import PressingActor
from src.models.retention.mechanism import (
    loosen_given_control,
    retention_given_arrival,
)


@dataclass(frozen=True)
class ValueCell:
    x_m: float
    y_m: float
    margin_s: float
    risk: Optional[float]
    control_prob: float
    marking_dist_m: float  # frozen at cell, not the fit covariate
    loosen_prob: float  # P(pass loosens structure | control, zone); 0.5 = unmodeled
    value: float


def outlet_value_fitted(
    control_prob: float,
    intercept_x_m: float,
    attack_sign: float = 1.0,
    loosen_prob: float = 0.5,
) -> float:
    """Safety-times-upside with the fitted control curve, not the assumed one.

    value = control x progress x loosen: the joint of arriving, sticking,
    and breaking shape, assuming independence until gate 5 fits the joint
    form (same null-to-beat pattern as retention's multiplicative start).
    loosen_prob defaults to 0.5 (unmodeled); the value surface passes the
    fitted zone rate via loosen_given_control. attack_sign and the
    stderr clip warning follow the old (cut) outlet_value contract.
    """
    if attack_sign not in (1.0, -1.0):
        raise ValueError(f"attack_sign must be +1 or -1, got {attack_sign}")
    x = intercept_x_m if attack_sign == 1.0 else PITCH_LENGTH_M - intercept_x_m
    if not 0.0 <= x <= PITCH_LENGTH_M:
        print(
            f"outlet_value_fitted: intercept_x_m={intercept_x_m} outside "
            f"[0, {PITCH_LENGTH_M}]: clipped to boundary",
            file=sys.stderr,
        )
    progress = min(1.0, max(0.0, x / PITCH_LENGTH_M))
    return round(control_prob * progress * loosen_prob, 4)


def value_surface(
    passer: PitchPoint,
    opponents: List[PressingActor],
    nx: int = 21,
    ny: int = 14,
    pace_k: float = 1.0,
) -> List[ValueCell]:
    """Per-cell (margin, risk, control, value) over a coarse pitch grid.

    Hypothetical receiver stands static at each cell center; pressers run
    the frozen snapshot. Risk follows decile_risk(pace_k); control
    follows the fitted exponential via retention_given_arrival; loosen
    follows the gate-5 zone table via loosen_given_control (controlled
    assumed: a hypothetical receiver is scored as if it controls —
    value is P(arrival) x P(control) x P(loosen | control), the joint
    under independence until gate 5 fits the joint form). Marking is
    frozen at the cell and carried for display.
    """
    cells: List[ValueCell] = []
    tid = 0
    for ix in range(nx):
        for iy in range(ny):
            x = (ix + 0.5) / nx * PITCH_LENGTH_M
            y = (iy + 0.5) / ny * PITCH_WIDTH_M
            probe = PressingActor(track_id=tid, team_id="own", pos_m=PitchPoint(x, y))
            tid += 1
            res = arrival_margin(probe, opponents, passer)
            if not res.margin_s > -99.0:
                cells.append(
                    ValueCell(
                        x_m=x,
                        y_m=y,
                        margin_s=res.margin_s,
                        risk=None,
                        control_prob=0.0,
                        marking_dist_m=99.0,
                        loosen_prob=0.0,
                        value=0.0,
                    )
                )
                continue
            dec = margin_decile(res.margin_s)
            ready = receiver_readiness(probe, passer)
            comp = retention_given_arrival(res, ready, res.marking_dist_m)
            zone = "def" if x < 35.0 else ("mid" if x < 70.0 else "att")
            loosen = loosen_given_control(zone, True)
            cells.append(
                ValueCell(
                    x_m=x,
                    y_m=y,
                    margin_s=res.margin_s,
                    risk=decile_risk(dec, pace_k),
                    control_prob=comp.control_prob,
                    marking_dist_m=res.marking_dist_m,
                    loosen_prob=loosen,
                    value=outlet_value_fitted(comp.control_prob, x, loosen_prob=loosen),
                )
            )
    return cells
