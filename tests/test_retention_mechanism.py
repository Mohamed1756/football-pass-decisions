"""Retention mechanism tests: hand-computed times, no plausibility asserts."""

import math

from src.core.geometry import PitchPoint
from src.models.retention.mechanism import (
    CONTROL_RADIUS_M,
    fitted_control_prob,
    label_touch,
    retention_given_arrival,
    touch_curve_exp,
)


def test_winner_curve_single_home():
    assert fitted_control_prob(-2.0) == 0.0  # below c0: lost, not small
    assert fitted_control_prob(1.3) == round(1.0 - math.exp(-0.40 * 2.80), 4)


def test_composition_threads_arrival_through_fit():
    from src.models.pressing.arrival import ArrivalResult
    from src.models.pressing.readiness import ReadinessResult

    # margin 1.9, latency 0.60 -> cushion 1.3 -> fitted prob
    arrival = ArrivalResult(9, 1.9, 0.96, 2.86, 1, 5.0)
    ready = ReadinessResult(9, 0.15, "pose", "open", 0.60)
    r = retention_given_arrival(arrival, ready, 5.0)
    assert r.cushion_s == ready.post_cushion_s(1.9) == 1.3
    assert r.control_prob == round(1.0 - math.exp(-0.40 * (1.3 + 1.50)), 4)
    assert r.marking_dist_m == 5.0  # carried, not yet scored


def test_composition_unscorable_stays_unscorable():
    from src.models.pressing.arrival import ArrivalResult
    from src.models.pressing.readiness import ReadinessResult

    arrival = ArrivalResult(9, -99.0, math.inf, math.inf, None, 99.0)
    ready = ReadinessResult(9, 0.25, "unknown", "unknown-facing", 0.70)
    r = retention_given_arrival(arrival, ready, 5.0)
    assert r.control_prob == 0.0  # never a fitted value
    assert r.cushion_s == -99.0


def test_label_touch_binary_radius():
    at = PitchPoint(80.0, 30.0)
    assert label_touch(PitchPoint(80.5, 30.0), at) is True
    assert label_touch(PitchPoint(80.0, 30.0 + CONTROL_RADIUS_M + 0.01), at) is False


def test_curves_winner_shape():
    # Shifted exponential: 0 below c0, near 1.0 on a wide cushion.
    assert touch_curve_exp(-2.0, 0.40, -1.50) == 0.0
    assert touch_curve_exp(1.0, 4.3) > 0.98
