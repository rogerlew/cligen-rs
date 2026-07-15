#!/usr/bin/env python3
"""Append the second optional-metadata correction and create freeze v3."""

from __future__ import annotations

import sys

from a5d1b_common import ARTIFACTS, CONTRACT, LOCK, canonical_sha256, load_json, sha256, write_json


PARENT = ARTIFACTS / "pre-outcome-freeze-v2.json"
ROOT_FREEZE = ARTIFACTS / "pre-outcome-freeze-v1.json"
AMENDMENT_001 = ARTIFACTS / "pre-outcome-freeze-amendment-001.json"
AMENDMENT_002 = ARTIFACTS / "pre-outcome-freeze-amendment-002.json"
FREEZE_V3 = ARTIFACTS / "pre-outcome-freeze-v3.json"
DIAGNOSTICS = ARTIFACTS / "inherited-path-diagnostics-v1.json"
EXPOSURE = ARTIFACTS / "exposure-ledger.md"
TOOLS = [
    "a5d1b_common.py",
    "freeze-a5d1b.py",
    "amend-freeze-a5d1b.py",
    "amend-freeze-a5d1b-v3.py",
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
        raise SystemExit("usage: amend-freeze-a5d1b-v3.py")
    if AMENDMENT_002.exists() or FREEZE_V3.exists():
        raise ValueError("A5d1b amendment 002/freeze v3 already exists")
    parent = load_json(PARENT)
    parent_body = dict(parent)
    parent_sha = parent_body.pop("freeze_sha256")
    if canonical_sha256(parent_body) != parent_sha:
        raise ValueError("freeze v2 identity mismatch")
    root = load_json(ROOT_FREEZE)
    root_sha = root["freeze_sha256"]
    count_outputs = [
        ARTIFACTS / "count-feasibility-results-v1.json",
        ARTIFACTS / "ordered-path-results-v1.json",
        ARTIFACTS / "a5d1b-results-v1.json",
        ARTIFACTS / "a5d1b-decision-v1.json",
    ]
    if any(path.exists() for path in count_outputs):
        raise ValueError("count/path/terminal output exists before amendment 002")
    old_hashes = parent["tool_hashes"]
    amendment = {
        "pre_outcome_freeze_amendment_schema_version": 1,
        "parent_freeze_sha256": parent_sha,
        "classification": "implementation-only null-safe optional solver metadata serialization",
        "contract_changed": False,
        "algorithm_changed": False,
        "tolerance_changed": False,
        "matrix_changed": False,
        "correction": "Treat scipy OptimizeResult.mip_node_count=None as JSON null; all optional HiGHS diagnostic fields are now nullable.",
        "trigger": "The amended first ak505769 joint linear MILP completed, then serialization raised TypeError on mip_node_count=None before status, objective, certificate, or aggregate was emitted.",
        "outcome_access_before_amendment": {
            "inherited_diagnostic_result": {"path": DIAGNOSTICS.name, "sha256": sha256(DIAGNOSTICS)},
            "first_count_station": "ak505769",
            "linear_solver_calls_completed": 2,
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
    write_json(AMENDMENT_002, amendment)
    freeze = {
        "pre_outcome_freeze_schema_version": 3,
        "state": "FROZEN-AFTER-INHERITED-DIAGNOSTICS-AND-TWO-ABORTED-FIRST-COUNT-CALLS-WITH-UNCHANGED-ALGORITHM",
        "development_only": True,
        "root_freeze_sha256": root_sha,
        "parent_freeze_sha256": parent_sha,
        "amendment_001_sha256": sha256(AMENDMENT_001),
        "amendment_sha256": sha256(AMENDMENT_002),
        "evidence_lock_sha256": sha256(LOCK),
        "contract_sha256": sha256(CONTRACT),
        "tool_hashes": {name: sha256(ARTIFACTS / name) for name in TOOLS},
        "count_matrix": parent["count_matrix"],
        "path_matrix": parent["path_matrix"],
        "expected_count_cells": parent["expected_count_cells"],
        "expected_path_cells_if_count_gate_passes": parent["expected_path_cells_if_count_gate_passes"],
        "diagnostic_freeze_sha256": root_sha,
        "inherited_diagnostic_results_sha256": sha256(DIAGNOSTICS),
        "count_outcome_files_existing_at_v3_freeze": [],
        "selection_rule": parent["selection_rule"],
        "confirmation_objects_in_scope": 0
    }
    freeze["freeze_sha256"] = canonical_sha256(freeze)
    write_json(FREEZE_V3, freeze)
    EXPOSURE.write_text(
        "# A5d1b Exposure Ledger\n\n"
        "Status: `AMENDED-V3-FROZEN-ZERO-CONFIRMATION-EXPOSURE`\n\n"
        "Allowed evidence remains limited to accepted repository authorities, the 17 already exposed A5a/A5b development stations, accepted A5d1 evidence, hash-reconciled ignored A5d1 working outputs, and synthetic fixtures.\n\n"
        "- Confirmation objects accessed: **0**\n"
        "- Confirmation target values or scores accessed: **0**\n"
        "- Confirmation WEPP responses accessed: **0**\n"
        "- Public candidate/profile identifiers created: **0**\n"
        "- Production or accepted public surfaces changed: **0**\n\n"
        "The v1 freeze preceded all A5d1b results. After inherited diagnostics, two first-station linear MILPs completed but optional `mip_gap=None` and then `mip_node_count=None` serialization aborted before any solver value, certificate, or aggregate was emitted. Amendments 001/002 changed only null-safe metadata handling; the contract, algorithm, tolerances, and matrices did not change.\n\n"
        f"The amended v3 tool freeze identity is `{freeze['freeze_sha256']}`.\n",
        encoding="utf-8",
    )
    print(f"A5d1b amended freeze v3: PASS ({freeze['freeze_sha256']})")


if __name__ == "__main__":
    main()

