"""Structure-delta tests: hand-computed frame arithmetic."""

from src.models.structure.mechanism import structure_delta


def test_press_broken_positive():
    # Nearest opp 2 m at receipt, 6 m at +3 s: pressure broken.
    d = structure_delta(
        (60.0, 34.0),
        (61.0, 34.0),
        {"P2": (60.0, 34.0)},
        {"P2": (61.0, 34.0)},
        {"P9": (62.0, 34.0)},
        {"P9": (67.0, 34.0)},
    )
    assert d.press_access_delta_m == 4.0


def test_compactness_stretched_positive():
    d = structure_delta(
        (60.0, 34.0),
        (61.0, 34.0),
        {},
        {},
        {"P9": (62.0, 34.0), "P8": (58.0, 34.0)},
        {"P9": (67.0, 34.0), "P8": (53.0, 34.0)},
    )
    # before mean: (2+2)/2=2; after: (6+8)/2=7
    assert d.compactness_delta_m == 5.0
