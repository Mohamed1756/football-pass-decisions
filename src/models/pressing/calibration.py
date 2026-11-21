"""Rank-space calibration: margin decile -> incompletion rate.

Absolute margins from frozen 360 shape are inflated (standing starts both
sides, no live pace), so the honest unit is rank: which outlets are tighter
than which. Fitted on 41,561 WC2022 completed/incomplete ground passes:

- bottom decile (margin <= ~1.0 s): 20.4% incompletion
- top decile (margin >= ~2.5 s): 0.2% incompletion
- ~93x failure gradient, monotone across all 10 deciles
- gradient holds within short/mid/long pass-length terciles (not a proxy)

Passers choose the safest outlet ~44% of the time on WC2022
(0.41-0.44 across the five 360 leagues); incompletion rises
with chosen rank (0.024 at rank 0 -> ~0.23 at rank 6+, rank 7 pooled).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Sequence, Tuple

# Decile upper edges (seconds) from the WC2022 fit, fitted values.
# Boundaries are descriptive of the calibration sample, not physics.
DECILE_EDGES_S: Tuple[float, ...] = (
    1.01,
    1.31,
    1.52,
    1.70,
    1.85,
    1.99,
    2.13,
    2.29,
    2.50,
    float("inf"),
)

# Observed incompletion rate per decile (index 0 = tightest).
DECILE_INCOMPLETION_RATE: Tuple[float, ...] = (
    0.204,
    0.131,
    0.085,
    0.049,
    0.033,
    0.023,
    0.016,
    0.009,
    0.006,
    0.002,
)

# Observed incompletion rate by chosen rank (0 = safest outlet).
# Rank 7 pools ranks 7+ (260 plays: 7:200, 8:56, 9:4).
RANK_INCOMPLETION_RATE: Tuple[float, ...] = (
    0.024,
    0.043,
    0.075,
    0.107,
    0.149,
    0.183,
    0.212,
    0.235,
)


@dataclass(frozen=True)
class OutletRank:
    margin_s: float
    rank: int
    n_outlets: int


def rank_outlets(margins_s: Sequence[float]) -> List[OutletRank]:
    """Rank outlets tightest-last: rank 0 is the safest (largest margin).

    Equal margins share no rank: ties break by input order (stable sort,
    first-listed tightest-ranked). No tie rule is inferred — callers that
    need tied ranks must quantize margins before calling.
    """
    order = sorted(range(len(margins_s)), key=lambda i: margins_s[i], reverse=True)
    ranks: List[OutletRank] = [None] * len(margins_s)  # type: ignore[list-item]
    for rank, idx in enumerate(order):
        ranks[idx] = OutletRank(
            margin_s=margins_s[idx], rank=rank, n_outlets=len(margins_s)
        )
    return ranks


def margin_decile(margin_s: float) -> int:
    """Decile bin (1-10) for a margin; 1 is tightest.

    Rejects non-finite input and the -99.0 unscorable sentinel: binning
    unscorable as decile 1 ("tightest, risk 0.204") is the silent-safe
    failure this instrument exists to prevent. Callers score unscorable
    via the margin_s == -99.0 check (see risk_surface), never via decile.

    Negative finite margins (non-viable outlets, press already wins)
    bin as decile 1 — bottom-decile risk, not higher. Mild
    extrapolation, acceptable for an ordering instrument, stated here
    so it is not silent.
    """

    if not math.isfinite(margin_s) or margin_s <= -99.0:
        raise ValueError(f"margin_decile needs a scored margin, got {margin_s}")
    for i, edge in enumerate(DECILE_EDGES_S):
        if margin_s <= edge:
            return i + 1
    return 10


def decile_risk(decile: int, pace_k: float = 1.0) -> float:
    """Fitted incompletion rate for a margin decile (1-10).

    pace_k scales the WC2022 rate for a slower/faster environment as a
    descriptive level shift, not physics: WWC 2023 fails ~1.5x the WC2022
    rate at equal frozen-shape margin (0.27 vs 0.20 bottom decile). Edges
    stay frozen; only levels move. Capped at 1.0, so ordering holds
    strictly below saturation — at high k the top deciles tie at 1.0
    (weak ordering, distinct margins identical risk).
    """
    if not 1 <= decile <= 10:
        raise ValueError(f"decile must be 1-10, got {decile}")
    if not math.isfinite(pace_k) or pace_k < 0:
        raise ValueError(f"pace_k must be finite and >= 0, got {pace_k}")
    return min(1.0, DECILE_INCOMPLETION_RATE[decile - 1] * pace_k)


def rank_risk(rank: int) -> float:
    """Fitted incompletion rate for a chosen rank (0 = safest, 7+ pooled)."""
    if rank < 0:
        raise ValueError(f"rank must be >= 0, got {rank}")
    return RANK_INCOMPLETION_RATE[min(rank, 7)]
