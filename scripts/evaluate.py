"""Eval harness: every gate falsifier plus the drift triggers, one command.

Runs the banked-pool checks the test suite pins (imported from the tests
themselves, not duplicated) and prints PASS/FAIL per gate. The pinned
tests read data/pooled paths directly, so --pool-dir is a forward hook
for the post-deployment harness, not an override today: run this on a
new pool by pointing a copy of the repo at it, or parametrize the tests
first. Anything printing FAIL on new data trips the recalibration
contract (rank-0 share shift > 0.05, frozen-edge d1 shift > 0.03,
control outside the banked match-clustered 95% CI). Read-only.
"""

import argparse
import sys
import traceback

sys.path.insert(0, ".")

CHECKS = [
    (
        "gate2",
        "choice shares pinned",
        "tests.test_choice_shares",
        "test_choice_shares_pinned",
    ),
    (
        "gate2",
        "top-2 robust to tail",
        "tests.test_choice_shares",
        "test_choice_top2_robust_to_tail",
    ),
    (
        "gate2",
        "viability separates rank-0",
        "tests.test_choice_viability",
        "test_rank0_separates_on_viability",
    ),
    ("gate2", "360 pool pinned", "tests.test_choice_sets_360", "test_360_pool_pinned"),
    (
        "gate2",
        "360 load gradient",
        "tests.test_choice_sets_360",
        "test_360_load_gradient_pinned",
    ),
    (
        "gate2",
        "360 set-size top-2",
        "tests.test_choice_sets_360",
        "test_360_set_size_top2_pinned",
    ),
    (
        "gate2",
        "360 value identity",
        "tests.test_choice_sets_360",
        "test_360_value_identity_pinned",
    ),
    (
        "gate3",
        "decile risk monotone",
        "tests.test_pressing_calibration",
        "test_decile_risk_monotone_fitted_gradient",
    ),
    (
        "gate4",
        "control fit NLLs",
        "tests.test_retention_fit",
        "test_winner_beats_null_and_assumed",
    ),
    ("gate4", "q1 bias pinned", "tests.test_retention_fit", "test_q1_bias_pinned"),
    ("gate1", "hold fit by zone", "tests.test_hold_fit", "test_hold_fit_pinned"),
    (
        "gate1",
        "hold fit controlled",
        "tests.test_hold_fit",
        "test_hold_fit_controlled_pinned",
    ),
    (
        "gate0",
        "formation table",
        "tests.test_formation_table",
        "test_formation_table_pinned",
    ),
    (
        "gate0",
        "formation loop null",
        "tests.test_formation_transition",
        "test_loop_null_pins",
    ),
    (
        "gate0/2",
        "load gradient monotone",
        "tests.test_choice_sets_table",
        "test_load_gradient_pinned",
    ),
    (
        "gate0/2",
        "choice sets zones",
        "tests.test_choice_sets_table",
        "test_choice_sets_zone_means",
    ),
    ("gate0/1", "load-vs-hold null", "tests.test_load_hold", "test_load_hold_null"),
    (
        "gate5",
        "structure zone means",
        "tests.test_structure_fit",
        "test_zone_means_pinned",
    ),
    (
        "gate5",
        "structure right tail",
        "tests.test_structure_fit",
        "test_right_tail_pinned",
    ),
]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool-dir", default="data/pooled")
    args = ap.parse_args()
    print(
        f"pool dir: {args.pool_dir} (override with --pool-dir for post-deployment pools)"
    )
    failures = 0
    for gate, name, mod_name, fn_name in CHECKS:
        try:
            mod = __import__(mod_name, fromlist=[fn_name])
            getattr(mod, fn_name)()
            print(f"PASS gate {gate}: {name}")
        except Exception:  # noqa: BLE001 - harness reports, never raises
            failures += 1
            print(f"FAIL gate {gate}: {name}")
            traceback.print_exc(limit=2)
    print(f"{len(CHECKS) - failures}/{len(CHECKS)} checks passed")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
