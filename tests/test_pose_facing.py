"""Pose facing tests: hand-built shoulder rigs, known angles."""

import math

import pytest

from src.io.pose import POSE_MAX_JOINT_ERR_CM, facing_from_joints, facing_source_tag


def _joints(lsh, rsh, mid, nose=None, neck=None, err=5.0):
    def entry(xyz):
        return {"xyz": list(xyz), "p90_mae_cm": err} if xyz is not None else None

    joints = {
        "lShoulder": entry(lsh),
        "rShoulder": entry(rsh),
        "midHip": entry(mid),
    }
    if nose is not None or neck is not None:
        joints["nose"] = entry(nose)
        joints["neck"] = entry(neck)
    return joints


def test_facing_cardinal_angles():
    # Facing +x (east): left shoulder north, nose east of mid-shoulder.
    east = _joints(
        (0.0, 0.2, 1.5), (0.0, -0.2, 1.5), (0.0, 0.0, 1.0), nose=(0.2, 0.0, 1.6)
    )
    assert facing_from_joints(east) == pytest.approx(0.0)
    # Facing -x: nose west.
    west = _joints(
        (0.0, 0.2, 1.5), (0.0, -0.2, 1.5), (0.0, 0.0, 1.0), nose=(-0.2, 0.0, 1.6)
    )
    assert abs(facing_from_joints(west)) == pytest.approx(math.pi)
    # Facing +y (north): shoulders span x, nose north.
    north = _joints(
        (-0.2, 0.0, 1.5), (0.2, 0.0, 1.5), (0.0, 0.0, 1.0), nose=(0.0, 0.2, 1.6)
    )
    assert facing_from_joints(north) == pytest.approx(math.pi / 2)


def test_neck_fallback_when_nose_missing():
    rig = _joints(
        (0.0, 0.2, 1.5), (0.0, -0.2, 1.5), (0.0, 0.0, 1.0), neck=(0.1, 0.05, 1.6)
    )
    assert facing_from_joints(rig) == pytest.approx(0.0, abs=0.5)


def test_unknown_without_forward_reference_or_axis():
    no_face = _joints((0.0, 0.2, 1.5), (0.0, -0.2, 1.5), (0.0, 0.0, 1.0))
    assert facing_from_joints(no_face) is None
    collapsed = _joints(
        (1.0, 1.0, 1.5), (1.0, 1.0, 1.5), (0.0, 0.0, 1.0), nose=(2.0, 1.0, 1.6)
    )
    assert facing_from_joints(collapsed) is None
    missing = _joints(None, (0.0, -0.2, 1.5), (0.0, 0.0, 1.0), nose=(0.2, 0.0, 1.6))
    assert facing_from_joints(missing) is None


def test_high_error_joints_gate_out():
    rig = _joints(
        (0.0, 0.2, 1.5),
        (0.0, -0.2, 1.5),
        (0.0, 0.0, 1.0),
        nose=(0.2, 0.0, 1.6),
        err=POSE_MAX_JOINT_ERR_CM + 0.1,
    )
    assert facing_from_joints(rig) is None
    ok = _joints(
        (0.0, 0.2, 1.5),
        (0.0, -0.2, 1.5),
        (0.0, 0.0, 1.0),
        nose=(0.2, 0.0, 1.6),
        err=POSE_MAX_JOINT_ERR_CM,
    )
    assert facing_from_joints(ok) == pytest.approx(0.0)


def test_source_tag_matches_resolve_facing():
    assert facing_source_tag() == "pose"
