"""Possession intervals: receipt to next event, stratified by exit.

Gate 1 slice 1: pure functions on hand slices only. No loader changes,
no fit, no banked intervals. The interval rule lives here so the bank
slice applies it unchanged to the 1,160 measured receptions.

An interval ends at the first of: pass attempt, loss of possession,
stoppage whistle. Cut off — dropped, not censored — when tracking
gaps, the half ends, or no next event is found: the pool is complete
intervals only, same reception-conditioning as gates 4-5.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple

ExitKind = Literal["pass", "loss", "stoppage"]


@dataclass(frozen=True)
class PossessionInterval:
    start_frame: int
    end_frame: int
    duration_s: float
    exit: ExitKind


def next_event(
    events: List[Tuple[int, str]],
    start_frame: int,
    frame_hz: float = 25.0,
) -> Optional[PossessionInterval]:
    """First event strictly after start_frame closes the interval.

    events: (frame, kind) sorted by frame, kind in {pass, loss,
    stoppage}. Returns None when no later event exists (cut off —
    caller drops the row, never imputes). Duration in seconds at the
    given frame rate.
    """
    for frame, kind in events:
        if frame <= start_frame:
            continue
        if kind not in ("pass", "loss", "stoppage"):
            continue
        return PossessionInterval(
            start_frame=start_frame,
            end_frame=frame,
            duration_s=round((frame - start_frame) / frame_hz, 3),
            exit=kind,  # type: ignore[arg-type]
        )
    return None

    """Gate 0 → gate 1 composition: pre-freeze shape carries no signal
    for hold duration (|corr| ≤ 0.10 on 1,159 rows, sep-vel splits
    2.26 vs 2.00 the flat way). Returns None by design, same pattern
    as freeze_given_delta: the slot is closed, not open.

    Callers wanting pre-freeze description use formation_window;
    callers wanting hold timing use next_event. The two don't compose
    into prediction — pinned in test_hold_freeze_null.
    """
    return None
