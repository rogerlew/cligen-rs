#!/usr/bin/env python3
"""Append the null-safe solver-metadata correction and create freeze v2."""

from __future__ import annotations

import sys

from a5d1b_common import ARTIFACTS, CONTRACT, LOCK, canonical_sha256, load_json, sha256, write_json


PARENT = ARTIFACTS / "pre-outcome-freeze-v1.json"
AMENDMENT = ARTIFACTS / "pre-outcome-freeze-amendment-001.json"
FREEZE_V2 = ARTIFACTS / "pre-outcome-freeze-v2.json"
DIAGNOSTICS = ARTIFACTS / "inherited-path-diagnostics-v1.json"
EXPOSURE = ARTIFACTS / "exposure-ledger.md"
TOOLS = [
    "a5d1b_common.py",
    "freeze-a5d1b.py",
    "amend-freeze-a5d1b.py",
    "run-synthetic-fixtures.py",
    "diagnose-inherited-paths.py",
    "solve-count-feasibility.py",
    "construct-ordered-paths.py",
    "archive-detailed-evidence.py",
    "finalize-a5d1b.py",
    "verify-a5d1b-package.py",
]


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: amend-freeze-a5d1b.py")
    if AMENDMENT.exists() or FREEZE_V2.exists():
        raise ValueError("A5d1b amendment/freeze v2 already exists")
    parent = load_json(PARENT)
    if not isinstance(parent, dict):
        raise ValueError("parent freeze is not an object")
    body = dict(parent)
    claimed = body.pop("freeze_sha256")
    if canonical_sha256(body) != claimed:
        raise ValueError("parent freeze identity mismatch")
    count_outputs = [
        ARTIFACTS / "count-feasibility-results-v1.json",
        ARTIFACTS / "ordered-path-results-v1.json",
        ARTIFACTS / "a5d1b-results-v1.json",
        ARTIFACTS / "a5d1b-decision-v1.json",
    ]
    if any(path.exists() for path in count_outputs):
        raise ValueError("count/path/terminal output exists before amendment")
    old_hashes = parent["tool_hashes"]
    amendment = {
        "pre_outcome_freeze_amendment_schema_version": 1,
        "parent_freeze_sha256": claimed,
        "classification": "implementation-only null-safe optional solver metadata serialization",
        "contract_changed": False,
        "algorithm_changed": False,
        "tolerance_changed": False,
        "matrix_changed": False,
        "correction": "Treat scipy OptimizeResult.mip_gap=None as JSON null instead of converting None to float.",
        "trigger": "The first ak505769 joint linear MILP completed, then serialization raised TypeError before status, objective, certificate, or aggregate was emitted.",
        "outcome_access_before_amendment": {
            "inherited_diagnostic_result": {"path": DIAGNOSTICS.name, "sha256": sha256(DIAGNOSTICS)},
            "first_count_station": "ak505769",
            "linear_solver_call_completed": True,
            "solver_status_or_objective_emitted": False,
            "count_certificate_files_written": 0,
            "count_aggregate_files_written": 0,
            "confirmation_objects_accessed": 0
        },
        "changed_tool_hashes": {
            "a5d1b_common.py": {"before": old_hashes["a5d1b_common.py"], "after": sha256(ARTIFACTS / "a5d1b_common.py")},
            "solve-count-feasibility.py": {"before": old_hashes["solve-count-feasibility.py"], "after": sha256(ARTIFACTS / "solve-count-feasibility.py")},
            "verify-a5d1b-package.py": {"before": old_hashes["verify-a5d1b-package.py"], "after": sha256(ARTIFACTS / "verify-a5d1b-package.py")}
        }
    }
    write_json(AMENDMENT, amendment)
    freeze = {
        "pre_outcome_freeze_schema_version": 2,
        "state": "FROZEN-AFTER-INHERITED-DIAGNOSTICS-AND-ABORTED-FIRST-COUNT-CALL-WITH-UNCHANGED-ALGORITHM",
        "development_only": True,
        "parent_freeze_sha256": claimed,
        "amendment_sha256": sha256(AMENDMENT),
        "evidence_lock_sha256": sha256(LOCK),
        "contract_sha256": sha256(CONTRACT),
        "tool_hashes": {name: sha256(ARTIFACTS / name) for name in TOOLS},
        "count_matrix": parent["count_matrix"],
        "path_matrix": parent["path_matrix"],
        "expected_count_cells": parent["expected_count_cells"],
        "expected_path_cells_if_count_gate_passes": parent["expected_path_cells_if_count_gate_passes"],
        "inherited_diagnostic_results_sha256": sha256(DIAGNOSTICS),
        "count_outcome_files_existing_at_v2_freeze": [],
        "selection_rule": parent["selection_rule"],
        "confirmation_objects_in_scope": 0
    }
    freeze["freeze_sha256"] = canonical_sha256(freeze)
    write_json(FREEZE_V2, freeze)
    EXPOSURE.write_text(
        "# A5d1b Exposure Ledger\n\n"
        "Status: `AMENDED-FROZEN-ZERO-CONFIRMATION-EXPOSURE`\n\n"
        "Allowed evidence remains limited to accepted repository authorities, the 17 already exposed A5a/A5b development stations, accepted A5d1 evidence, hash-reconciled ignored A5d1 working outputs, and synthetic fixtures.\n\n"
        "- Confirmation objects accessed: **0**\n"
        "- Confirmation target values or scores accessed: **0**\n"
        "- Confirmation WEPP responses accessed: **0**\n"
        "- Public candidate/profile identifiers created: **0**\n"
        "- Production or accepted public surfaces changed: **0**\n\n"
        "The v1 freeze preceded all A5d1b results. After inherited diagnostics, the first `ak505769` linear MILP completed but optional `mip_gap=None` serialization aborted before status, objective, certificate, or aggregate emission. Amendment 001 changed only null-safe metadata handling; the contract, algorithm, tolerances, and matrices did not change.\n\n"
        f"The amended tool freeze identity is `{freeze['freeze_sha256']}`.\n",
        encoding="utf-8",
    )
    print(f"A5d1b amended freeze v2: PASS ({freeze['freeze_sha256']})")


if __name__ == "__main__":
    main()
