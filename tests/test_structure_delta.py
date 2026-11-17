"""Structure-delta tests: hand-computed frame arithmetic."""

from src.models.structure.mechanism import OPEN_MAN_RADIUS_M, structure_delta


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
    assert OPEN_MAN_RADIUS_M == 5.0


def test_open_men_counts_separation():
    # Mate 6 m from nearest opp after, 2 m before: +1 open man.
    d = structure_delta(
        (60.0, 34.0),
        (61.0, 34.0),
        {"P2": (60.0, 34.0), "P4": (50.0, 20.0)},
        {"P2": (61.0, 34.0), "P4": (50.0, 20.0)},
        {"P9": (62.0, 34.0), "P8": (51.0, 21.0)},
        {"P9": (70.0, 34.0), "P8": (51.0, 21.0)},
    )
    assert d.open_men_delta == 1  # P9 left; P8 still tight on P4


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
