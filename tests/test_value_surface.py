"""Value surface tests: hand-computed cell, unscorable, ordering."""

from src.core.geometry import PitchPoint
from src.models.pressing.types import PressingActor
from src.models.value_surface import outlet_value_fitted, value_surface


def _actor(tid, x, y, team="opp"):
    return PressingActor(track_id=tid, team_id=team, pos_m=PitchPoint(x, y))


def test_surface_covers_grid_with_control_and_value():
    cells = value_surface(PitchPoint(52.5, 34.0), [_actor(1, 70.0, 34.0)], nx=7, ny=4)
    assert len(cells) == 28
    assert all(
        c.control_prob is not None and 0.0 <= c.control_prob <= 1.0 for c in cells
    )
    assert all(c.value >= 0.0 for c in cells)
    assert all(c.margin_s > -99.0 for c in cells)


def test_no_opponents_yields_zero_value_not_safe():
    cells = value_surface(PitchPoint(52.5, 34.0), [], nx=5, ny=3)
    assert cells and all(c.risk is None for c in cells)
    assert all(c.control_prob == 0.0 and c.value == 0.0 for c in cells)


def test_outlet_value_fitted_prefers_forward_control():
    # Default loosen 0.5 (unmodeled): value = control x progress x 0.5.
    assert outlet_value_fitted(0.9, 80.0) > outlet_value_fitted(0.9, 30.0)
    assert outlet_value_fitted(0.9, 80.0) == round(0.9 * 80.0 / 105.0 * 0.5, 4)
    assert outlet_value_fitted(0.0, 80.0) == 0.0  # no control, no value
    # Full loosen: control x progress, the gate-4 surface.
    assert outlet_value_fitted(0.9, 80.0, loosen_prob=1.0) == round(
        0.9 * 80.0 / 105.0, 4
    )


def test_hand_computed_cell_pins_full_chain():
    # Exact grid center (7.5, 8.5): verify the chain end to end.
    from src.models.pressing.arrival import arrival_margin
    from src.models.pressing.readiness import receiver_readiness
    from src.models.pressing.types import PressingActor as PA
    from src.models.retention.mechanism import retention_given_arrival

    probe = PA(track_id=0, team_id="own", pos_m=PitchPoint(7.5, 8.5))
    opp = PA(track_id=1, team_id="opp", pos_m=PitchPoint(70.0, 34.0))
    passer = PitchPoint(52.5, 34.0)
    res = arrival_margin(probe, [opp], passer)
    ready = receiver_readiness(probe, passer)
    comp = retention_given_arrival(res, ready, res.marking_dist_m)
    cells = value_surface(passer, [opp], nx=7, ny=4)
    cell = [c for c in cells if c.x_m == 7.5 and c.y_m == 8.5][0]
    assert cell.margin_s == res.margin_s
    assert cell.control_prob == comp.control_prob
    assert cell.loosen_prob == 0.356  # def-zone fitted rate, not default
    assert cell.value == outlet_value_fitted(
        comp.control_prob, cell.x_m, loosen_prob=0.356
    )
