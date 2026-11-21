"""Tests for the risk surface: structure, pace ordering, bounds."""

from src.core.geometry import PitchPoint
from src.models.pressing.types import PressingActor
from src.models.risk_surface import risk_surface
from src.models.value_surface import value_surface


def _actor(tid, x, y, team="opp"):
    return PressingActor(track_id=tid, team_id=team, pos_m=PitchPoint(x, y))


def test_surface_covers_grid_and_bounds_risk():
    cells = risk_surface(PitchPoint(52.5, 34.0), [_actor(1, 70.0, 34.0)], nx=7, ny=4)
    assert len(cells) == 28
    assert all(c.risk is not None and 0.0 <= c.risk <= 1.0 for c in cells)
    assert all(c.margin_s > -99.0 for c in cells)


def test_pace_k_shifts_levels_not_order():
    base = risk_surface(PitchPoint(52.5, 34.0), [_actor(1, 70.0, 34.0)], nx=7, ny=4)
    fast = risk_surface(
        PitchPoint(52.5, 34.0), [_actor(1, 70.0, 34.0)], nx=7, ny=4, pace_k=1.5
    )
    assert len(base) == len(fast)
    # same ordering: sort by one, check other is monotone
    order = sorted(range(len(base)), key=lambda i: base[i].risk)
    fr = [fast[i].risk for i in order]
    assert all(fr[i] <= fr[i + 1] + 1e-9 for i in range(len(fr) - 1))
    # levels shift up (capped at 1.0)
    assert sum(f.risk for f in fast) >= sum(b.risk for b in base)


def test_no_opponents_yields_unscorable_not_safe():
    cells = risk_surface(PitchPoint(52.5, 34.0), [], nx=5, ny=3)
    assert cells and all(c.risk is None for c in cells)
    assert all(c.margin_s == -99.0 for c in cells)


def test_value_grid_agrees_with_risk_grid():
    # The two grid loops are duplicated on purpose (rule of three: two
    # uses, no helper until the third surface). This pins their
    # agreement so the duplication is enforced, not coincidental:
    # extract a shared helper if a third surface appears.
    passer = PitchPoint(52.5, 34.0)
    opps = [_actor(1, 70.0, 34.0), _actor(2, 30.0, 20.0)]
    rc = {(c.x_m, c.y_m): c for c in risk_surface(passer, opps, nx=7, ny=4)}
    vc = {(c.x_m, c.y_m): c for c in value_surface(passer, opps, nx=7, ny=4)}
    assert set(rc) == set(vc) and len(rc) == 28
    assert all(rc[k].margin_s == vc[k].margin_s for k in rc)
    assert all(rc[k].risk == vc[k].risk for k in rc)
    rc0 = risk_surface(passer, [], nx=5, ny=3)
    vc0 = value_surface(passer, [], nx=5, ny=3)
    assert all(c.risk is None for c in rc0)
    assert all(c.risk is None for c in vc0)
    assert all(c.value == 0.0 and c.control_prob == 0.0 for c in vc0)
