"""Branch credit readout tests: hand-computed formula checks.

The readout script itself runs read-only over banked pools + raw and
prints aggregates (documented in choice.md); these tests pin the
definitions on hand values, not on pool output. No raw, no banking.
"""


def _credit_regret(values, chosen):
    best = max(values)
    mean = sum(values) / len(values)
    return round(values[chosen] - mean, 4), round(best - values[chosen], 4)


def _b_resid(controlled, expected):
    return round(float(controlled) - expected, 4)


def test_credit_rewards_beating_the_set_mean():
    # Values [0.5, 0.3, 0.2]: mean 1/3; choosing best earns 0.5-1/3.
    credit, regret = _credit_regret([0.5, 0.3, 0.2], 0)
    assert credit == round(0.5 - 1 / 3, 4)
    assert regret == 0.0
    # Choosing worst: negative credit, full-regret gap.
    credit, regret = _credit_regret([0.5, 0.3, 0.2], 2)
    assert credit == round(0.2 - 1 / 3, 4)
    assert regret == 0.3


def test_credit_zero_on_flat_set():
    # Flat freeze asks nothing: any branch equals the mean, regret zero.
    credit, regret = _credit_regret([0.4, 0.4, 0.4], 1)
    assert credit == 0.0
    assert regret == 0.0


def test_b_resid_sign_direction():
    # Controlled below expectation reads negative (underperformance).
    assert _b_resid(True, 0.8) == 0.2
    assert _b_resid(False, 0.8) == -0.8
    assert _b_resid(True, 0.0) == 1.0
