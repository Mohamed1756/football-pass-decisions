"""B-to-A linkage prototype: chain freezes into possession sequences.

For each match, order banked retention rows by pass_idx and link k->k+1
iff target_id(k) resolves to the passer pid of k+1 (reverse lookup on
team + short name) and hold_exit(k) == 'pass'. Prints linkage rate,
chain-length distribution, gap distribution (seconds at 25 Hz), and
collision/drop counts. Read-only; Task B (banking) only on a pass.
"""

import statistics
import sys

sys.path.insert(0, ".")

from src.io.idsse import _load_roster

POOL_PATH = "data/pooled/idsse_retention_labeled.pkl"
MATCHES = ["J03WMX", "J03WN1", "J03WOH", "J03WOY", "J03WQQ", "J03WR9", "J03WPY"]
FRAME_HZ = 25.0


def main() -> None:
    import pickle

    rows = pickle.load(open(POOL_PATH, "rb"))
    by_match = {}
    for r in rows:
        by_match.setdefault(r["match"], []).append(r)

    total = linked = 0
    collisions = 0
    gaps = []
    lengths = []
    for m in MATCHES:
        c = "000001" if m in ("J03WMX", "J03WN1") else "000002"
        mp = f"/tmp/idsse_raw/DFL_02_01_matchinformation_DFL-COM-{c}_DFL-MAT-{m}.xml"
        _length, _width, teams, names = _load_roster(mp)
        rev = {}
        for pid, nm in names.items():
            rev.setdefault((nm, teams.get(pid)), []).append(pid)
        seq = sorted(by_match.get(m, []), key=lambda r: r["pass_idx"])
        chain_len = 1
        for a, b in zip(seq, seq[1:]):
            total += 1
            # Passer and target share a side; key on the passer's own side.
            cands = rev.get((b["passer"], teams.get(b["target_id"])))
            if not cands or len(cands) != 1:
                collisions += 1
                lengths.append(chain_len)
                chain_len = 1
                continue
            if a["target_id"] == cands[0] and a["hold_exit"] == "pass":
                linked += 1
                gaps.append((b["pass_idx"] - a["pass_idx"]) / FRAME_HZ)
                chain_len += 1
            else:
                lengths.append(chain_len)
                chain_len = 1
        lengths.append(chain_len)
    print(f"links: {linked}/{total} = {linked / total:.3f}")
    print(f"collisions/ambiguous: {collisions}")
    print(f"chain length: median={statistics.median(lengths)} max={max(lengths)}")
    print(
        f"gap_s: median={statistics.median(gaps):.1f} "
        f"p90={sorted(gaps)[int(len(gaps) * 0.9)]:.1f} max={max(gaps):.1f}"
    )
    print("half_cross_note: gaps above ~900 s span the break; counted, not cut")


if __name__ == "__main__":
    main()
