"""Formation window: press access and separation velocity at the freeze.

Gate 0 descriptors that move: nearest-opponent distance to ball (state)
and its rate of change over [-5 s, 0] (derivative). Open-man counts cut:
repositioning without separation (+0.01 to +0.21 everywhere) — noise
with a name. See gate5.md for the same cut on the resolution side.
Affordance volume sits beside the window: viable-set size plus margin
entropy over the frozen choice-set margins, same gate-0 status —
describes the freeze, rates nothing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class FormationWindow:
    press_access_at_freeze_m: float
    separation_velocity_ms: float


@dataclass(frozen=True)
class AffordanceVolume:
    n_viable: int
    entropy_bits: float
    effective_options: float


def affordance_volume(
    margins_s: Sequence[float], viability_thr_s: float = 0.0
) -> AffordanceVolume:
    """Choice load at the freeze from frozen choice-set margins.

    Viable = finite margin above viability_thr_s (default 0.0, the
    physical viability line in arrival.md: margin > 0). The -99.0
    unscorable sentinel never counts as viable. Probabilities are
    linear in margin over the viable subset only: p_j = m_j / sum(m).
    Linear needs all m_j > 0, which viability_thr_s >= 0 guarantees;
    a negative threshold would admit negative probabilities, so it
    raises. Entropy is base-2 (bits); effective options = 2**H.
    Empty or single-viable sets read (0, 0.0, 0.0) / (1, 0.0, 1.0):
    no choice, no load.
    """
    if not math.isfinite(viability_thr_s) or viability_thr_s < 0.0:
        raise ValueError(
            f"viability_thr_s must be finite and >= 0, got {viability_thr_s}"
        )
    viable = [
        m for m in margins_s if math.isfinite(m) and m > viability_thr_s and m > -99.0
    ]
    n = len(viable)
    if n <= 1:
        return AffordanceVolume(
            n_viable=n, entropy_bits=0.0, effective_options=float(n)
        )
    total = sum(viable)
    entropy = -sum((m / total) * math.log2(m / total) for m in viable)
    return AffordanceVolume(
        n_viable=n,
        entropy_bits=round(entropy, 3),
        effective_options=round(2.0**entropy, 3),
    )


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
