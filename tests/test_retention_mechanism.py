"""Retention mechanism tests: hand-computed times, no plausibility asserts."""

from src.core.geometry import PitchPoint
from src.models.retention.mechanism import (
    CONTROL_RADIUS_M,
    UNKNOWN_FACING_TURN_S,
    disrupt_time_s,
    label_touch,
    retention_margin_s,
    touch_curve_exp,
    touch_curve_logistic,
    touch_need_s,
)


def test_touch_need_known_facing_adds_turn():
    assert touch_need_s(0.15, True) == 0.60  # 0.45 + open plant
    assert touch_need_s(0.70, True) == 1.15  # 0.45 + full flip


def test_touch_need_unknown_takes_placeholder_mean():
    assert UNKNOWN_FACING_TURN_S == 0.39
    assert touch_need_s(0.0, False) == 0.84  # 0.45 + 0.39, never floor 0
    assert touch_need_s(0.25, False) == 0.84  # arg ignored when unknown


def test_disrupt_time_distance_over_speed():
    assert disrupt_time_s(3.0, 3.0) == 1.0
    assert disrupt_time_s(1.5, 8.5) == 0.176  # sprint cap fallback


def test_disrupt_time_zero_speed_is_inf():
    import math

    assert disrupt_time_s(3.0, 0.0) == math.inf
    assert disrupt_time_s(3.0, -1.0) == math.inf


def test_retention_margin_same_shape_as_arrival():
    m = retention_margin_s(0.84, 1.0)
    assert m.margin_s == 0.16  # disrupt - need, control holds iff > 0
    assert retention_margin_s(1.0, 0.5).margin_s == -0.5


def test_label_touch_binary_radius():
    at = PitchPoint(80.0, 30.0)
    assert label_touch(PitchPoint(80.5, 30.0), at) is True
    assert label_touch(PitchPoint(80.0, 30.0 + CONTROL_RADIUS_M + 0.01), at) is False


def test_curves_agree_at_mid_cushion_disagree_at_tail():
    # Both near 1.0 on a wide cushion; exponential rises faster early.
    assert touch_curve_logistic(1.0, 15.0, 0.15) > 0.99
    assert touch_curve_exp(1.0, 4.3) > 0.98
    assert touch_curve_exp(0.1, 4.3) > touch_curve_logistic(0.1, 15.0, 0.15)
