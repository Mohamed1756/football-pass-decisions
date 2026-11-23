"""360 loader tests: hand-built slices, hand-computed values."""

import json

from src.io.three_sixty import (
    _parse_timestamp,
    _read_freeze,
    _read_passes,
    choose_outlet,
)


def _write(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f)


def test_canonical_mapping_centers_halfway(tmp_path):
    p = tmp_path / "fr.jsonl"
    p.write_text(
        json.dumps(
            [
                {
                    "event_uuid": "e1",
                    "visible_area": [],
                    "freeze_frame": [
                        {
                            "teammate": True,
                            "actor": False,
                            "keeper": False,
                            "location": [60.0, 40.0],
                        },
                        {
                            "teammate": True,
                            "actor": True,
                            "keeper": False,
                            "location": [0.0, 0.0],
                        },
                        {
                            "teammate": False,
                            "actor": False,
                            "keeper": True,
                            "location": [120.0, 80.0],
                        },
                    ],
                }
            ]
        )
    )
    mates = _read_freeze(str(p))["e1"]
    assert len(mates) == 3  # opponents kept, flagged not-mate
    assert mates[0].pos_m == (52.5, 34.0)
    assert mates[0].is_actor is False and mates[0].is_mate is True
    assert mates[1].is_actor is True
    assert mates[2].is_mate is False


def test_ground_filter_and_outcome_default(tmp_path):
    p = tmp_path / "ev.json"
    _write(
        str(p),
        [
            {
                "id": "a",
                "type": {"name": "Pass"},
                "team": {"name": "Home"},
                "period": 1,
                "timestamp": "00:01:10.500",
                "location": [60.0, 40.0],
                "pass": {
                    "recipient": {"name": "R"},
                    "height": {"name": "Ground Pass"},
                    "end_location": [90.0, 40.0],
                },
            },
            {
                "id": "b",
                "type": {"name": "Pass"},
                "team": {"name": "Home"},
                "period": 1,
                "timestamp": "00:02:00.000",
                "location": [60.0, 40.0],
                "pass": {
                    "recipient": {"name": "R"},
                    "height": {"name": "High Pass"},
                    "end_location": [90.0, 40.0],
                },
            },
            {
                "id": "c",
                "type": {"name": "Carry"},
                "team": {"name": "Home"},
                "period": 1,
                "location": [60.0, 40.0],
            },
        ],
    )
    rows = _read_passes(str(p))
    assert len(rows) == 1  # high ball and non-pass dropped
    r = rows[0]
    assert r.complete is True  # absent outcome = successful
    assert r.timestamp_s == 70.5
    assert r.end_pos_m == (90.0 / 120.0 * 105.0, 40.0 / 80.0 * 68.0)


def test_choose_outlet_excludes_actor_and_measures():
    from src.io.three_sixty import FrozenOutlet

    mates = [
        FrozenOutlet(pos_m=(80.0, 34.0), is_actor=True, is_keeper=False),
        FrozenOutlet(pos_m=(70.0, 34.0), is_actor=False, is_keeper=False),
        FrozenOutlet(pos_m=(60.0, 34.0), is_actor=False, is_keeper=False),
    ]
    idx, d = choose_outlet(mates, (71.0, 34.0))
    assert idx == 1
    assert d == 1.0
    assert choose_outlet([], (0.0, 0.0)) == (None, float("inf"))


def test_timestamp_parsing():
    assert _parse_timestamp("00:01:10.500") == 70.5
    assert _parse_timestamp("45:00.0") == 2700.0
    assert _parse_timestamp(None) == 0.0
    assert _parse_timestamp("bogus") == 0.0
