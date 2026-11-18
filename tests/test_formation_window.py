"""Formation window tests: hand-computed pre-freeze geometry."""

from src.models.formation.mechanism import formation_window


def test_freeze_shape_press_access():
    w = formation_window(
        (50.0, 34.0),
        {"P2": (60.0, 34.0)},
        {"P9": (52.0, 34.0)},
        {},
    )
    assert w.press_access_at_freeze_m == 2.0


def test_separation_velocity_positive_when_opening():
    w = formation_window(
        (50.0, 34.0),
        {"P2": (60.0, 34.0)},
        {"P9": (56.0, 34.0)},
        {"P2": [(58.0, 34.0), (59.0, 34.0), (60.0, 34.0)]},
    )
    # d: 2.0 -> 3.0 -> 4.0 over 2 steps = 1.0/frame
    assert w.separation_velocity_ms == 1.0


def test_missing_tracks_skipped_not_zeroed():
    w = formation_window((50.0, 34.0), {}, {}, {})
    assert w.separation_velocity_ms == 0.0
