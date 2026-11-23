"""Regen-diff gate: generated figs 8-12 plus L1 13a-d must match banked SVGs.

Change a pinned constant -> rerun the builders -> commit the SVGs,
same task. This test enforces that workflow via the figures.py CLI.
"""

import subprocess
import sys


def test_figures_match_banked():
    proc = subprocess.run(
        [sys.executable, "scripts/figures.py", "check"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
