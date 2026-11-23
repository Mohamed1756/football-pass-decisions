"""L1 freeze schematics: one SVG per pinned freeze, banked fields only.

Grammar (fixed): vertical outlet stack, rank 0 top, bar length propto
margin, rank label left, tau line down the stack (right = viable),
chosen ringed, best-unchosen hollow-marked, header annotations right.
Degenerate states drawn, never hidden: singleton slot + tag,
unscorable hatched stack + risk=None tag. No coordinates, no motion.
"""

from __future__ import annotations

import hashlib
import pickle
import statistics

CHOICE_SETS_PATH = "data/pooled/idsse_choice_sets_labeled.pkl"
RETENTION_LABELED_PATH = "data/pooled/idsse_retention_labeled.pkl"

TAU_S: float = 0.0


def row_hash(match: str, pass_idx: int, target_id: str) -> str:
    return hashlib.blake2b(
        f"{match}|{pass_idx}|{target_id}".encode(), digest_size=6
    ).hexdigest()


def _zone(x_m: float) -> str:
    return "def" if x_m < 35.0 else ("mid" if x_m < 70.0 else "att")


def l1_rows():
    """Four pinned rows: (kind, banked row dict or synthetic dict)."""
    sets = pickle.load(open(CHOICE_SETS_PATH, "rb"))
    ret = pickle.load(open(RETENTION_LABELED_PATH, "rb"))
    rx = {(r["match"], r["pass_idx"], r["target_id"]): r for r in ret}
    joined = []
    for s in sets:
        r = rx[(s["match"], s["pass_idx"], s["target_id"])]
        joined.append((s, r))

    def row_dict(s, r):
        order = sorted(
            range(len(s["margins"])), key=lambda i: s["margins"][i], reverse=True
        )
        return {
            "match": s["match"],
            "pass_idx": s["pass_idx"],
            "target_id": s["target_id"],
            "hash": row_hash(s["match"], s["pass_idx"], s["target_id"]),
            "margins": list(s["margins"]),
            "rank_order": order,
            "chosen_idx": s["outlet_pids"].index(s["target_id"]),
            "n_outlets": s["n_outlets"],
            "n_viable": s["n_viable"],
            "entropy_bits": s["entropy_bits"],
            "effective_options": s["effective_options"],
            "pre_press_m": r["pre_press_m"],
            "pre_sep_vel": r["pre_sep_vel"],
            "zone": _zone(r["recept_x_m"]),
            "controlled": r["controlled"],
            "delta_press_m": r["delta_press_m"],
            "hold_s": r["hold_s"],
            "hold_exit": r["hold_exit"],
            "synthetic": False,
        }

    mid9 = [
        p
        for p in joined
        if _zone(p[1]["recept_x_m"]) == "mid" and p[0]["n_viable"] == 9
    ]
    med = statistics.median([p[0]["entropy_bits"] for p in mid9])
    median = min(mid9, key=lambda p: abs(p[0]["entropy_bits"] - med))
    controlled = [
        p for p in joined if p[1]["controlled"] and p[1]["delta_press_m"] is not None
    ]
    tail = max(controlled, key=lambda p: p[1]["delta_press_m"])
    smallest = min(
        joined, key=lambda p: (p[0]["n_viable"], p[0]["match"], p[0]["pass_idx"])
    )
    synth = {
        "match": "SYNTH",
        "pass_idx": -1,
        "target_id": "none",
        "hash": row_hash("SYNTH", -1, "none"),
        "margins": [-99.0, -99.0, -99.0],
        "rank_order": [0, 1, 2],
        "chosen_idx": -1,
        "n_outlets": 3,
        "n_viable": 0,
        "entropy_bits": 0.0,
        "effective_options": 0.0,
        "pre_press_m": None,
        "pre_sep_vel": None,
        "zone": "mid",
        "controlled": False,
        "delta_press_m": None,
        "hold_s": None,
        "hold_exit": None,
        "synthetic": True,
    }
    out = [
        ("median", row_dict(*median)),
        ("tail", row_dict(*tail)),
        ("smallest", row_dict(*smallest)),
        ("unscorable", synth),
    ]
    return out


def render_freeze_schematic(row: dict) -> str:
    """Deterministic SVG for one joined freeze row. Pure, stdlib only."""
    margins = row["margins"]
    n = len(margins)
    order = row["rank_order"]
    chosen = row["chosen_idx"]
    best = order[0] if order else -1
    lo = min(min(margins), TAU_S, 0.0)
    hi = max(max(margins), TAU_S, 0.0)
    span = hi - lo if hi > lo else 1.0

    def bx(v):
        return 150 + (v - lo) / span * 450.0

    H = 120 + n * 44
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 %d" role="img">' % H,
        "<title>Freeze schematic</title>",
        '<pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse">'
        '<path d="M0,8 L8,0" stroke="#8c959f" stroke-width="1.5"/></pattern>',
    ]
    subtitle = "%s %s %s · zone %s · ctrl %s · hold %s/%s" % (
        row["match"],
        row["pass_idx"],
        row["target_id"],
        row["zone"],
        row["controlled"],
        row["hold_s"],
        row["hold_exit"],
    )
    parts.append(
        '<text x="150" y="30" font-size="16" fill="#24292f">Freeze: safest-first outlet stack</text>'
    )
    parts.append(
        '<text x="150" y="52" font-size="12" fill="#57606a">%s · hash %s%s</text>'
        % (subtitle, row["hash"], " · SYNTHETIC" if row["synthetic"] else "")
    )
    parts.append(
        '<text x="150" y="72" font-size="12" fill="#57606a">n=%d viable=%d entropy=%.2f bits · pre_press=%s pre_sep=%s · Δpress=%s</text>'
        % (
            row["n_outlets"],
            row["n_viable"],
            row["entropy_bits"],
            row["pre_press_m"],
            row["pre_sep_vel"],
            row["delta_press_m"],
        )
    )
    tx = bx(TAU_S)
    parts.append(
        '<line x1="%.0f" y1="90" x2="%.0f" y2="%d" stroke="#cf222e" stroke-width="1.5" stroke-dasharray="5 4"/>'
        % (tx, tx, H - 20)
    )
    parts.append(
        '<text x="%.0f" y="84" font-size="11" fill="#cf222e">τ=%.1f viable →</text>'
        % (tx + 4, TAU_S)
    )
    for pos, idx in enumerate(order):
        y = 108 + pos * 44
        m = margins[idx]
        w = max(bx(m) - 150, 2)
        if m <= -99.0:
            parts.append(
                '<rect x="150" y="%d" width="450" height="26" fill="url(#hatch)" stroke="#8c959f"/>'
                % y
            )
        else:
            fill = "#0969da" if m > TAU_S else "#8c959f"
            parts.append(
                '<rect x="150" y="%d" width="%.0f" height="26" fill="%s"/>'
                % (y, w, fill)
            )
        parts.append(
            '<text x="130" y="%d" text-anchor="end" font-size="12" fill="#24292f">r%d</text>'
            % (y + 18, pos)
        )
        parts.append(
            '<text x="%d" y="%d" font-size="11" fill="#57606a">%.2f</text>'
            % (160 + w, y + 18, m)
        )
        if idx == chosen:
            parts.append(
                '<rect x="144" y="%d" width="%.0f" height="38" fill="none" stroke="#1a7f37" stroke-width="3"/>'
                % (y - 6, w + 12)
            )
            parts.append(
                '<text x="%.0f" y="%d" font-size="11" fill="#1a7f37">chosen</text>'
                % (160 + w + 8, y + 18)
            )
        elif idx == best and chosen != -1:
            parts.append(
                '<circle cx="%.0f" cy="%d" r="7" fill="none" stroke="#9a6700" stroke-width="2"/>'
                % (160 + w + 8, y + 13)
            )
            parts.append(
                '<text x="%.0f" y="%d" font-size="11" fill="#9a6700">best unchosen</text>'
                % (176 + w, y + 18)
            )
    if row["n_viable"] <= 1 and not row["synthetic"]:
        parts.append(
            '<text x="150" y="%d" font-size="12" fill="#9a6700">singleton set: counted, never scored</text>'
            % (H - 24)
        )
    if row["synthetic"]:
        parts.append(
            '<text x="150" y="%d" font-size="12" fill="#57606a">risk=None · unscorable freeze, never a margin</text>'
            % (H - 24)
        )
    parts.append("</svg>")
    return "\n".join(parts)


def build_all():
    out = {}
    for kind, row in l1_rows():
        out[f"docs/figs/fig13_freeze_{kind}.svg"] = render_freeze_schematic(row)
    return out


def _by_kind(kind):
    for k, row in l1_rows():
        if k == kind:
            return render_freeze_schematic(row)
    raise KeyError(kind)


def build_median():
    return _by_kind("median")


def build_tail():
    return _by_kind("tail")


def build_smallest():
    return _by_kind("smallest")


def build_unscorable():
    return _by_kind("unscorable")


if __name__ == "__main__":
    for path, svg in build_all().items():
        open(path, "w").write(svg)
        print(f"wrote {path}")
