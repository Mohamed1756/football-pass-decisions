"""Pipeline test: one outlet end to end, hand-computed."""

import pytest

from src.core.geometry import PitchPoint
from src.models.pipeline import run_outlet
from src.models.pressing.types import PressingActor


def test_run_outlet_threads_gates():
    rec = PressingActor(track_id=9, team_id="own", pos_m=PitchPoint(86.0, 25.0))
    opp = PressingActor(track_id=1, team_id="opp", pos_m=PitchPoint(87.5, 26.5))
    out = run_outlet(rec, [opp], PitchPoint(100.0, 29.0), source="tracking")
    assert out.margin_s > -99.0
    assert out.control_prob > 0.0
    assert out.loosen_prob_given_control == 0.258  # att-zone fitted rate


def test_run_outlet_frozen_raises():
    rec = PressingActor(track_id=9, team_id="own", pos_m=PitchPoint(86.0, 25.0))
    opp = PressingActor(track_id=1, team_id="opp", pos_m=PitchPoint(87.5, 26.5))
    with pytest.raises(ValueError):
        run_outlet(rec, [opp], PitchPoint(100.0, 29.0))
    with pytest.raises(ValueError):
        run_outlet(rec, [opp], PitchPoint(100.0, 29.0), source="broadcast")


def test_run_outlet_unscorable_propagates():
    rec = PressingActor(track_id=9, team_id="own", pos_m=PitchPoint(5.0, 34.0))
    out = run_outlet(rec, [], PitchPoint(100.0, 29.0), source="tracking")
    assert out.risk is None
    assert (
        out.control_prob == 0.0
        and out.loosen_prob_given_control == 0.0
        and out.value == 0.0
    )
