"""L1 freeze schematics: pinned rows, deterministic bytes, degenerates.

Row identity pins the four L1 slots (median/tail/smallest banked,
unscorable synthetic). Determinism: same row -> byte-identical SVG.
Degenerate coverage: singleton and hatched-unscorable render without
raising. Drift itself is enforced by test_figures_match_banked, which
rebuilds through scripts/figures.py (L1 builders registered there).
"""

import sys

sys.path.insert(0, "scripts")

from freeze_schematic import l1_rows, render_freeze_schematic

PINNED = {
    "median": ("J03WN1", 11156, "DFL-OBJ-J016C3", "b9351ab9029e"),
    "tail": ("J03WR9", 33038, "DFL-OBJ-0026MI", "9af1a677e3e4"),
    "smallest": ("J03WMX", 112405, "DFL-OBJ-0002DR", "deb13a81fdfe"),
    "unscorable": ("SYNTH", -1, "none", "fa754eadc587"),
}


def test_l1_rows_pinned():
    rows = dict(l1_rows())
    assert sorted(rows) == ["median", "smallest", "tail", "unscorable"]
    for kind, (match, pass_idx, target, digest) in PINNED.items():
        r = rows[kind]
        assert (r["match"], r["pass_idx"], r["target_id"]) == (match, pass_idx, target)
        assert r["hash"] == digest


def test_l1_deterministic_bytes():
    rows = dict(l1_rows())
    for kind, row in rows.items():
        assert render_freeze_schematic(row) == render_freeze_schematic(row), kind


def test_l1_degenerate_renders():
    rows = dict(l1_rows())
    synth = rows["unscorable"]
    assert synth["synthetic"] is True
    svg = render_freeze_schematic(synth)
    assert "url(#hatch)" in svg and "risk=None" in svg
    single = dict(synth)
    single.update(
        {
            "margins": [1.5],
            "rank_order": [0],
            "chosen_idx": 0,
            "n_outlets": 1,
            "n_viable": 1,
            "synthetic": False,
        }
    )
    one = render_freeze_schematic(single)
    assert "counted, never scored" in one
