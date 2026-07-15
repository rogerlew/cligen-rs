#!/usr/bin/env python3
"""Record the post-outcome incumbent correction and create execution freeze v4."""

from __future__ import annotations

import sys

from a5d1b_common import ARTIFACTS, CONTRACT, LOCK, canonical_sha256, load_json, sha256, write_json


PARENT = ARTIFACTS / "pre-outcome-freeze-v3.json"
ROOT_FREEZE = ARTIFACTS / "pre-outcome-freeze-v1.json"
AMENDMENT_003 = ARTIFACTS / "post-outcome-correction-amendment-003.json"
FREEZE_V4 = ARTIFACTS / "corrected-execution-freeze-v4.json"
EXPOSURE = ARTIFACTS / "exposure-ledger.md"
HISTORY = ARTIFACTS / "history/v3-tools"
INCUMBENT_FIXTURES = ARTIFACTS / "incumbent-acceptance-fixture-results-v1.json"
INVALIDATED = [
    "invalidated-v3-count-feasibility-results-v1.json",
    "invalidated-v3-ordered-path-results-v1.json",
    "invalidated-v3-detailed-evidence-manifest-v1.json",
    "invalidated-v3-detailed-evidence-v1.tar.gz",
    "invalidated-v3-a5d1b-results-v1.json",
    "invalidated-v3-a5d1b-decision-v1.json",
    "invalidated-v3-count-semantic-replay-audit-v1.json",
]
TOOLS = [
    "a5d1b_common.py",
    "freeze-a5d1b.py",
    "amend-freeze-a5d1b.py",
    "amend-freeze-a5d1b-v3.py",
    "amend-freeze-a5d1b-v4.py",
    "run-synthetic-fixtures.py",
    "run-incumbent-acceptance-fixtures.py",
    "diagnose-inherited-paths.py",
    "solve-count-feasibility.py",
    "construct-ordered-paths.py",
    "archive-detailed-evidence.py",
    "finalize-a5d1b.py",
    "verify-count-witnesses.py",
    "verify-a5d1b-package.py",
]


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: amend-freeze-a5d1b-v4.py")
    if AMENDMENT_003.exists() or FREEZE_V4.exists():
        raise ValueError("A5d1b amendment 003/freeze v4 already exists")
    parent = load_json(PARENT)
    parent_body = dict(parent)
    parent_sha = parent_body.pop("freeze_sha256")
    if canonical_sha256(parent_body) != parent_sha:
        raise ValueError("freeze v3 identity mismatch")
    for name, digest in parent["tool_hashes"].items():
        if sha256(HISTORY / name) != digest:
            raise ValueError(f"historical v3 tool identity mismatch: {name}")
    invalidated = {name: {"bytes": (ARTIFACTS / name).stat().st_size, "sha256": sha256(ARTIFACTS / name)} for name in INVALIDATED}
    old_results = load_json(ARTIFACTS / "invalidated-v3-count-feasibility-results-v1.json")
    if old_results["linear_necessary_system_witness_count"] != 0 or old_results["count_pass_count"] != 0:
        raise ValueError("unexpected invalidated v3 aggregate")
    corrected_outputs = [
        ARTIFACTS / "count-feasibility-results-v1.json",
        ARTIFACTS / "ordered-path-results-v1.json",
        ARTIFACTS / "a5d1b-results-v1.json",
        ARTIFACTS / "a5d1b-decision-v1.json",
        ARTIFACTS / "count-witness-replay-audit-v1.json",
        ARTIFACTS / "detailed-evidence-v1.tar.gz",
    ]
    if any(path.exists() for path in corrected_outputs):
        raise ValueError("corrected outcome exists before execution freeze v4")
    amendment = {
        "post_outcome_correction_amendment_schema_version": 1,
        "parent_freeze_sha256": parent_sha,
        "classification": "post-outcome implementation correction after independent scientific and accuracy review",
        "scientific_contract_changed": False,
        "algorithm_implementation_changed": True,
        "tolerance_changed": False,
        "matrix_changed": False,
        "correction": "Accept a solver incumbent only after independent integrality, bound, and primal-constraint replay, regardless of OptimizeResult.success; replay every accepted initial incumbent against the exact nonlinear count contract before continuing sequential centering.",
        "trigger": "The exposed v3 implementation treated OptimizeResult.success as feasibility. HiGHS time-limit status 1 retained one joint and six separate-100 incumbents that were discarded without count extraction or exact replay.",
        "v3_outcome_exposure": {
            "reported_joint_linear_witnesses": old_results["linear_necessary_system_witness_count"],
            "reported_joint_exact_witnesses": old_results["count_pass_count"],
            "joint_status1_objective_present_count": 1,
            "separate_100_status1_objective_present_count": 6,
            "confirmation_objects_accessed": 0,
        },
        "invalidated_v3_outcomes": invalidated,
        "historical_v3_tool_directory": "history/v3-tools",
        "historical_v3_tool_hashes": parent["tool_hashes"],
        "corrected_execution_outputs_existing_at_freeze": [],
    }
    write_json(AMENDMENT_003, amendment)
    root = load_json(ROOT_FREEZE)
    freeze = {
        "corrected_execution_freeze_schema_version": 4,
        "state": "FROZEN-AFTER-V3-OUTCOME-INVALIDATION-AND-BEFORE-CORRECTED-COUNT-EXECUTION",
        "development_only": True,
        "root_prospective_freeze_sha256": root["freeze_sha256"],
        "parent_freeze_sha256": parent_sha,
        "amendment_sha256": sha256(AMENDMENT_003),
        "evidence_lock_sha256": sha256(LOCK),
        "contract_sha256": sha256(CONTRACT),
        "incumbent_acceptance_fixture_results_sha256": sha256(INCUMBENT_FIXTURES),
        "tool_hashes": {name: sha256(ARTIFACTS / name) for name in TOOLS},
        "count_matrix": parent["count_matrix"],
        "path_matrix": parent["path_matrix"],
        "expected_count_cells": parent["expected_count_cells"],
        "expected_path_cells_if_count_gate_passes": parent["expected_path_cells_if_count_gate_passes"],
        "diagnostic_freeze_sha256": parent["diagnostic_freeze_sha256"],
        "inherited_diagnostic_results_sha256": parent["inherited_diagnostic_results_sha256"],
        "corrected_count_outcome_files_existing_at_v4_freeze": [],
        "selection_rule": parent["selection_rule"],
        "confirmation_objects_in_scope": 0,
    }
    freeze["freeze_sha256"] = canonical_sha256(freeze)
    write_json(FREEZE_V4, freeze)
    EXPOSURE.write_text(
        "# A5d1b Exposure Ledger\n\n"
        "Status: `CORRECTED-V4-FROZEN-ZERO-CONFIRMATION-EXPOSURE`\n\n"
        "Allowed evidence remains limited to accepted repository authorities, the 17 already exposed A5a/A5b development stations, accepted A5d1 evidence, hash-reconciled ignored A5d1 working outputs, and synthetic fixtures.\n\n"
        "- Confirmation objects accessed: **0**\n"
        "- Confirmation target values or scores accessed: **0**\n"
        "- Confirmation WEPP responses accessed: **0**\n"
        "- Public candidate/profile identifiers created: **0**\n"
        "- Production or accepted public surfaces changed: **0**\n\n"
        "The v1 freeze preceded every A5d1b result. Amendments 001/002 repaired null-safe optional metadata serialization before any count result was emitted. The completed v3 run was then invalidated after independent review found that time-limit incumbents were discarded by an incorrect `OptimizeResult.success` gate. Amendment 003 is explicitly post-outcome and changes the algorithm implementation, while retaining the scientific contract, tolerances, and matrices. The v3 outputs and tool bytes remain hash-bound history.\n\n"
        f"The corrected v4 execution freeze identity is `{freeze['freeze_sha256']}`.\n",
        encoding="utf-8",
    )
    print(f"A5d1b corrected execution freeze v4: PASS ({freeze['freeze_sha256']})")


if __name__ == "__main__":
    main()
