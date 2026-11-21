"""Banked-figure builder: SVG from pinned test constants, no raw needed.

Each generated figure (8-12) reads its numbers from the test file that
pins them, so a generated figure can never drift from the evidence.
Frozen figures (1, 3, 5, 6, 7) have no builder; see data/pooled/README
Figure provenance. Run on demand, not in CI.
"""

import sys

sys.path.insert(0, ".")


def retention_deciles() -> str:
    """Gate-4 control-by-cushion-decile: obs vs fitted exp curve."""
    from tests.test_retention_fit import DECILE_FIT, DECILE_OBS, FIT_C0, FIT_LAM, POOL_N

    # log-ish y mapping over [0.25, 0.75]
    def y(v: float) -> float:
        lo, hi = 0.25, 0.75
        return 476 - (v - lo) / (hi - lo) * 360

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560" role="img">',
        "<title>Retention: control by cushion decile</title>",
        '<text x="500" y="32" text-anchor="middle" font-size="19" fill="#24292f">Tighter cushions lose the ball — fitted exponential holds</text>',
        f'<text x="500" y="54" text-anchor="middle" font-size="13" fill="#57606a">Control rate by post-touch cushion decile (own tenths) · {POOL_N:,} IDSSE receptions · dots observed, line fitted (lam {FIT_LAM:.2f}, c0 {FIT_C0:.2f})</text>',
        '<rect x="90" y="76" width="620" height="400" fill="none" stroke="#d0d7de" stroke-width="1.5"/>',
    ]
    for i in range(1, 11):
        x = 121 + (i - 1) * 62
        parts.append(
            f'<text x="{x}" y="496" text-anchor="middle" font-size="12" fill="#24292f">{i}</text>'
        )
    parts.append(
        '<text x="400" y="528" text-anchor="middle" font-size="13" fill="#57606a">cushion decile (1 = tightest post-touch time, 10 = loosest)</text>'
    )
    for v, lab in [(0.3, "0.3"), (0.5, "0.5"), (0.7, "0.7")]:
        parts.append(
            f'<text x="82" y="{y(v):.0f}" text-anchor="end" font-size="12" fill="#57606a">{lab}</text>'
        )
    parts.append(
        '<text x="34" y="280" text-anchor="middle" font-size="13" fill="#57606a" transform="rotate(-90 34 280)">share of receptions controlled</text>'
    )
    fit_pts = " ".join(f"{121 + i * 62},{y(v):.0f}" for i, v in enumerate(DECILE_FIT))
    parts.append(
        f'<polyline points="{fit_pts}" fill="none" stroke="#0969da" stroke-width="2.5"/>'
    )
    for i, v in enumerate(DECILE_OBS):
        x = 121 + i * 62
        parts.append(f'<circle cx="{x}" cy="{y(v):.0f}" r="4" fill="#cf222e"/>')
    parts.append(
        '<g font-size="13" fill="#24292f"><circle cx="750" cy="120" r="4" fill="#cf222e"/>'
        '<text x="762" y="125">observed</text>'
        '<line x1="744" y1="144" x2="756" y2="144" stroke="#0969da" stroke-width="2.5"/>'
        '<text x="762" y="149">fitted exp</text>'
        '<text x="740" y="180" font-weight="bold">Takeaway</text>'
        '<text x="740" y="202" font-size="13">Monotone to q9; q10 dips</text>'
        '<text x="740" y="220" font-size="13">on n=115 — same tail as</text>'
        '<text x="740" y="238" font-size="13">the arrival gradient.</text></g>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def resolution_heatmap() -> str:
    """Gate-5 press-access delta by zone x control: 6 pinned cells."""
    from tests.test_retention_fit import POOL_N
    from tests.test_structure_fit import ZONE_MEANS

    # diverging color: blue (loosens, +) to red (tightens, -), white at 0
    def color(v: float) -> str:
        v = max(-2.6, min(0.5, v))
        if v >= 0:
            t = v / 0.5
            return f"rgb({int(255 - 200 * (1 - t))},{int(255 - 120 * (1 - t))},{int(255 - 200 * (1 - t))})"
        t = -v / 2.6
        return f"rgb({int(255 - 60 * t)},{int(200 - 120 * t)},{int(200 - 80 * t)})"

    zones = ["def", "mid", "att"]
    rows = [(True, "controlled"), (False, "lost")]
    mid_loosen = ZONE_MEANS[("mid", False)][1]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560" role="img">',
        "<title>Resolution: press-access change by zone and control</title>",
        '<text x="500" y="32" text-anchor="middle" font-size="19" fill="#24292f">Controlled receptions read tighter on average</text>',
        f'<text x="500" y="54" text-anchor="middle" font-size="13" fill="#57606a">Mean press-access delta (m) by reception zone and first touch · {POOL_N:,} IDSSE receptions · red = converges, blue = loosens</text>',
    ]
    for ri, (ctl, lab) in enumerate(rows):
        y = 120 + ri * 130
        parts.append(
            f'<text x="200" y="{y + 45}" text-anchor="end" font-size="14" fill="#24292f">{lab}</text>'
        )
        for ci, z in enumerate(zones):
            x = 240 + ci * 200
            n, press, _ = ZONE_MEANS[(z, ctl)]
            parts.append(
                f'<rect x="{x}" y="{y}" width="180" height="100" fill="{color(press)}" stroke="#d0d7de" stroke-width="1.5"/>'
            )
            parts.append(
                f'<text x="{x + 90}" y="{y + 45}" text-anchor="middle" font-size="22" fill="#24292f">{"+" if press > 0 else ""}{press:.2f}</text>'
            )
            parts.append(
                f'<text x="{x + 90}" y="{y + 68}" text-anchor="middle" font-size="12" fill="#57606a">n={n}</text>'
            )
    for ci, z in enumerate(zones):
        parts.append(
            f'<text x="{240 + ci * 200 + 90}" y="105" text-anchor="middle" font-size="14" fill="#24292f">{z}</text>'
        )
    parts.append(
        '<g font-size="13" fill="#24292f">'
        '<text x="740" y="400" font-weight="bold">Takeaway</text>'
        '<text x="740" y="422" font-size="13">Tighter on average given</text>'
        '<text x="740" y="440" font-size="13">control; only mid reads</text>'
        f'<text x="740" y="458" font-size="13">looser on failed receipt ({mid_loosen:+.2f}).</text></g>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def freeze_schematic() -> str:
    """Gate-0 pre-freeze shape by zone: press access + separation velocity."""
    from tests.test_formation_table import FORMATION_BY_ZONE

    zones = ["def", "mid", "att"]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560" role="img">',
        "<title>Freeze: pre-pass shape by zone</title>",
        '<text x="500" y="32" text-anchor="middle" font-size="19" fill="#24292f">Freezes start pressed; men close down, not open up</text>',
        f'<text x="500" y="54" text-anchor="middle" font-size="13" fill="#57606a">Mean press access (m, blue) + separation velocity (m/s, red) 5 s before the pass · {sum(v[0] for v in FORMATION_BY_ZONE.values()):,} IDSSE receptions with full tracks</text>',
        '<rect x="90" y="76" width="620" height="400" fill="none" stroke="#d0d7de" stroke-width="1.5"/>',
    ]

    # Two panels like fig11: left bars = press access (m), right dots =
    # sep. velocity (m/s, labeled). Killed the position-as-value dots.
    def bh(v: float) -> float:
        return (v - 4.0) / 4.0 * 300  # press 4..8 m -> height

    def ry(v: float) -> float:
        return 420 - (v + 0.5) / 0.5 * 300  # sep -0.5..0 -> y

    for ci, z in enumerate(zones):
        x0 = 121 + ci * 200
        _, press, sep = FORMATION_BY_ZONE[z]
        h = bh(press)
        parts.append(
            f'<rect x="{x0}" y="{420 - h:.0f}" width="80" height="{h:.0f}" fill="#0969da"/>'
        )
        parts.append(
            f'<text x="{x0 + 40}" y="500" text-anchor="middle" font-size="12" fill="#24292f">{z}</text>'
        )
        parts.append(
            f'<text x="{x0 + 40}" y="{410 - h:.0f}" text-anchor="middle" font-size="13" fill="#24292f">{press:.2f} m</text>'
        )
        parts.append(
            f'<circle cx="{x0 + 140}" cy="{ry(sep):.0f}" r="6" fill="#cf222e"/>'
        )
        parts.append(
            f'<text x="{x0 + 140}" y="500" text-anchor="middle" font-size="12" fill="#57606a">sep</text>'
        )
        parts.append(
            f'<text x="{x0 + 140}" y="{ry(sep) - 12:.0f}" text-anchor="middle" font-size="12" fill="#cf222e">{sep:.3f}</text>'
        )
    for v in (5.0, 6.0, 7.0):
        yy = 420 - (v - 4.0) / 4.0 * 300
        parts.append(
            f'<line x1="90" y1="{yy:.0f}" x2="710" y2="{yy:.0f}" stroke="#d0d7de" stroke-width="1" stroke-dasharray="3 5"/>'
        )
        parts.append(
            f'<text x="82" y="{yy + 4:.0f}" text-anchor="end" font-size="12" fill="#0969da">{v:.1f} m</text>'
        )
    parts.append(
        '<g font-size="13" fill="#24292f">'
        '<rect x="744" y="112" width="14" height="14" fill="#0969da"/><text x="762" y="124">press access (bar, left m)</text>'
        '<circle cx="751" cy="140" r="6" fill="#cf222e"/><text x="762" y="145">sep. velocity (dot, labeled)</text>'
        '<text x="740" y="180" font-weight="bold">Takeaway</text>'
        '<text x="740" y="202" font-size="13">Attacking freezes start</text>'
        f'<text x="740" y="220" font-size="13">most pressed ({FORMATION_BY_ZONE["att"][1]:.2f} m);</text>'
        '<text x="740" y="238" font-size="13">men close down everywhere</text>'
        "</g>"
    )
    parts.append("</svg>")
    return "\n".join(parts)


def hold_by_zone() -> str:
    """Gate-1 hold medians + pass-within-3s by zone, exits stratified."""
    from tests.test_hold_fit import HOLD_BY_ZONE, POOL_N

    zones = ["def", "mid", "att"]
    mid_med, mid_p3 = HOLD_BY_ZONE["mid"][1], HOLD_BY_ZONE["mid"][2]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560" role="img">',
        "<title>Attempt: hold duration by zone</title>",
        '<text x="500" y="32" text-anchor="middle" font-size="19" fill="#24292f">Mid releases quickest; edges hold longer</text>',
        f'<text x="500" y="54" text-anchor="middle" font-size="13" fill="#57606a">Median hold (s, bars) + pass-within-3 s (dots) by reception zone · {POOL_N:,} IDSSE intervals</text>',
        '<rect x="90" y="76" width="620" height="400" fill="none" stroke="#d0d7de" stroke-width="1.5"/>',
    ]

    def bx(v: float) -> float:
        return 90 + (v - 1.0) / 2.0 * 620  # hold 1..3 s

    def by(v: float) -> float:
        return 476 - (v - 0.5) / 0.3 * 360  # p3 0.5..0.8

    # Two panels: left bars = median hold (s), right dots = pass-in-3s rate.
    # Killed the position-as-value encoding — a dot's x meant nothing.
    for ci, z in enumerate(zones):
        x0 = 121 + ci * 200
        _, med, p3, npass, _ = HOLD_BY_ZONE[z]
        # left panel bar: hold seconds, 1.5..2.75 range mapped to height
        h = (med - 1.5) / 1.25 * 300
        parts.append(
            f'<rect x="{x0}" y="{420 - h:.0f}" width="80" height="{h:.0f}" fill="#0969da"/>'
        )
        parts.append(
            f'<text x="{x0 + 40}" y="500" text-anchor="middle" font-size="12" fill="#24292f">{z}</text>'
        )
        parts.append(
            f'<text x="{x0 + 40}" y="{410 - h:.0f}" text-anchor="middle" font-size="13" fill="#24292f">{med:.2f}s</text>'
        )
        # right dot: pass rate on shared vertical position scale per column
        ry = 420 - (p3 - 0.55) / 0.2 * 300
        parts.append(f'<circle cx="{x0 + 140}" cy="{ry:.0f}" r="6" fill="#cf222e"/>')
        parts.append(
            f'<text x="{x0 + 140}" y="500" text-anchor="middle" font-size="12" fill="#57606a">p3</text>'
        )
        parts.append(
            f'<text x="{x0 + 140}" y="{ry - 12:.0f}" text-anchor="middle" font-size="12" fill="#cf222e">{p3:.3f}</text>'
        )
    # left axis: seconds
    for v in (1.5, 2.0, 2.5):
        yy = 420 - (v - 1.5) / 1.25 * 300
        parts.append(
            f'<line x1="90" y1="{yy:.0f}" x2="710" y2="{yy:.0f}" stroke="#d0d7de" stroke-width="1" stroke-dasharray="3 5"/>'
        )
        parts.append(
            f'<text x="82" y="{yy + 4:.0f}" text-anchor="end" font-size="12" fill="#0969da">{v:.1f} s</text>'
        )
    parts.append(
        '<g font-size="13" fill="#24292f">'
        '<rect x="744" y="112" width="14" height="14" fill="#0969da"/><text x="762" y="124">median hold (bar, left s)</text>'
        '<circle cx="751" cy="140" r="6" fill="#cf222e"/><text x="762" y="145">pass-in-3s (dot, labeled)</text>'
        '<text x="740" y="180" font-weight="bold">Takeaway</text>'
        '<text x="740" y="202" font-size="13">Mid moves it quickest</text>'
        f'<text x="740" y="220" font-size="13">({mid_med:.2f} s, {mid_p3:.3f}); edges</text>'
        '<text x="740" y="238" font-size="13">hold longer vs set</text>'
        '<text x="740" y="256" font-size="13">defenses.</text></g>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def choice_shares() -> str:
    """Gate-2 choice shares per rank, five leagues overlaid."""
    from tests.test_choice_shares import CHOICE_SHARES, CHOICE_TOTAL

    leagues = ["wc2022", "euro2020", "laliga", "euro2024", "wwc2023"]
    colors = ["#0969da", "#1a7f37", "#8250df", "#cf7122", "#cf222e"]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 560" role="img">',
        "<title>Choice: rank shares by league</title>",
        f'<text x="500" y="32" text-anchor="middle" font-size="19" fill="#24292f">Safest outlet takes ~{sum(v[0] for v in CHOICE_SHARES.values()) / len(CHOICE_SHARES):.2f} everywhere</text>',
        f'<text x="500" y="54" text-anchor="middle" font-size="13" fill="#57606a">Share choosing each rank (0 = safest, 7+ pooled) · five 360 leagues, {CHOICE_TOTAL:,} passes</text>',
        '<rect x="90" y="76" width="620" height="400" fill="none" stroke="#d0d7de" stroke-width="1.5"/>',
    ]

    def y(v: float) -> float:
        import math

        return 476 - (math.log10(max(v, 0.005)) + 2.3) / 2.0 * 360

    for li, lg in enumerate(leagues):
        pts = " ".join(
            f"{121 + d * 78},{y(v):.0f}" for d, v in enumerate(CHOICE_SHARES[lg])
        )
        parts.append(
            f'<polyline points="{pts}" fill="none" stroke="{colors[li]}" stroke-width="2.5"/>'
        )
    for d in range(8):
        x = 121 + d * 78
        lab = str(d) if d < 7 else "7+"
        parts.append(
            f'<text x="{x}" y="496" text-anchor="middle" font-size="12" fill="#24292f">{lab}</text>'
        )
    parts.append(
        '<text x="400" y="528" text-anchor="middle" font-size="13" fill="#57606a">chosen rank (0 = safest outlet)</text>'
    )
    for v, lab in [(0.4, "0.4"), (0.1, "0.1"), (0.03, "0.03"), (0.008, "0.008")]:
        parts.append(
            f'<line x1="90" y1="{y(v):.0f}" x2="710" y2="{y(v):.0f}" stroke="#d0d7de" stroke-width="1" stroke-dasharray="3 5"/>'
        )
        parts.append(
            f'<text x="82" y="{y(v) + 4:.0f}" text-anchor="end" font-size="12" fill="#57606a">{lab}</text>'
        )
    parts.append(
        '<text x="34" y="280" text-anchor="middle" font-size="13" fill="#57606a" transform="rotate(-90 34 280)">share choosing rank (log scale)</text>'
    )
    for li, lg in enumerate(leagues):
        yy = 120 + li * 24
        parts.append(
            f'<line x1="740" y1="{yy}" x2="768" y2="{yy}" stroke="{colors[li]}" stroke-width="3"/>'
            f'<text x="776" y="{yy + 5}" font-size="13" fill="#24292f">{lg}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    import pathlib
    import sys

    builders = {
        "retention": retention_deciles,
        "resolution": resolution_heatmap,
        "freeze": freeze_schematic,
        "hold": hold_by_zone,
        "choice": choice_shares,
    }
    paths = {
        "retention": "docs/figs/fig8_retention_deciles.svg",
        "resolution": "docs/figs/fig9_resolution_heatmap.svg",
        "freeze": "docs/figs/fig10_freeze_schematic.svg",
        "hold": "docs/figs/fig11_hold_by_zone.svg",
        "choice": "docs/figs/fig12_choice_shares.svg",
    }
    name = sys.argv[1] if len(sys.argv) > 1 else "retention"
    if name == "check":
        # Regen-diff gate: rebuild all five in memory, fail on drift.
        # Change a pin -> rerun builders -> commit SVGs, same task.
        drifted = []
        for key, build in builders.items():
            if pathlib.Path(paths[key]).read_text() != build():
                drifted.append(paths[key])
        if drifted:
            print("drifted figures (rerun builders and commit):")
            print("\n".join(drifted))
            sys.exit(1)
        print("figures match banked")
    else:
        svg = builders[name]()
        open(paths[name], "w").write(svg)
        print(f"wrote {paths[name]}")
