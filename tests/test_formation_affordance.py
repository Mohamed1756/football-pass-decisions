"""Affordance volume tests: hand-computed viable-set size + margin entropy."""

import math

import pytest

from src.models.formation.mechanism import affordance_volume


def test_two_viable_peaked():
    # viable [2.5, 1.0], sum 3.5, p = [5/7, 2/7]
    # H = -(5/7*log2(5/7) + 2/7*log2(2/7)) = 0.863
    a = affordance_volume([2.5, 1.0, -0.5])
    assert a.n_viable == 2
    assert a.entropy_bits == 0.863
    assert a.effective_options == 1.819


def test_three_viable_flat_near_max():
    # viable [2.5, 2.4, 2.3], near-uniform, H just under log2(3) = 1.585
    a = affordance_volume([2.5, 2.4, 2.3])
    assert a.n_viable == 3
    assert a.entropy_bits == 1.584
    assert a.effective_options == 2.998


def test_three_viable_peaked_low_entropy():
    # viable [0.1, 0.05, 3.0]: one dominant outlet, H = 0.320
    a = affordance_volume([0.1, 0.05, 3.0])
    assert a.n_viable == 3
    assert a.entropy_bits == 0.320
    assert a.effective_options == 1.248


def test_sentinel_and_inf_excluded():
    a = affordance_volume([2.5, -99.0, math.inf, -0.3])
    assert a.n_viable == 1
    assert a.entropy_bits == 0.0
    assert a.effective_options == 1.0


def test_empty_and_nan():
    a = affordance_volume([])
    assert (a.n_viable, a.entropy_bits, a.effective_options) == (0, 0.0, 0.0)
    b = affordance_volume([float("nan"), -99.0])
    assert b.n_viable == 0


def test_threshold_strict_and_guarded():
    # strict > : 1.0 itself not viable at thr 1.0
    a = affordance_volume([2.5, 1.0, 0.5], viability_thr_s=1.0)
    assert a.n_viable == 1
    with pytest.raises(ValueError):
        affordance_volume([2.5, 1.0], viability_thr_s=-0.1)
    with pytest.raises(ValueError):
        affordance_volume([2.5, 1.0], viability_thr_s=math.inf)
