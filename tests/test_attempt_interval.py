"""Possession interval tests: hand-computed event chains."""

from src.models.attempt.mechanism import next_event


def test_interval_closes_on_first_later_event():
    events = [(100, "pass"), (150, "loss"), (200, "stoppage")]
    iv = next_event(events, 90)
    assert iv is not None
    assert (iv.end_frame, iv.exit) == (100, "pass")
    assert iv.duration_s == 0.4  # 10 frames at 25 Hz


def test_interval_skips_start_frame_and_unknown_kinds():
    events = [(100, "dribble"), (100, "pass"), (150, "loss")]
    iv = next_event(events, 100)
    assert iv is not None
    assert (iv.end_frame, iv.exit) == (150, "loss")


def test_no_later_event_is_cutoff_not_zero():
    events = [(100, "pass")]
    assert next_event(events, 100) is None
    assert next_event(events, 150) is None
    assert next_event([], 100) is None
