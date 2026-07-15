#!/usr/bin/env python3
"""Record the corrected-aggregate import fix and create execution freeze v5."""

from __future__ import annotations

import sys

from a5d1b_common import ARTIFACTS, CONTRACT, LOCK, canonical_sha256, load_json, sha256, write_json


PARENT = ARTIFACTS / "corrected-execution-freeze-v4.json"
AMENDMENT_004 = ARTIFACTS / "post-outcome-correction-amendment-004.json"
FREEZE_V5 = ARTIFACTS / "corrected-execution-freeze-v5.json"
EXPOSURE = ARTIFACTS / "exposure-ledger.md"
HISTORY = ARTIFACTS / "history/v4-tools"
INVALIDATED_ARCHIVE = ARTIFACTS / "invalidated-v4-count-certificates-v1.tar.gz"
INVALIDATED_MANIFEST = ARTIFACTS / "invalidated-v4-count-certificates-manifest-v1.json"
TOOLS = [
    "a5d1b_common.py",
    "freeze-a5d1b.py",
    "amend-freeze-a5d1b.py",
    "amend-freeze-a5d1b-v3.py",
    "amend-freeze-a5d1b-v4.py",
    "amend-freeze-a5d1b-v5.py",
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
        raise SystemExit("usage: amend-freeze-a5d1b-v5.py")
    if AMENDMENT_004.exists() or FREEZE_V5.exists():
        raise ValueError("A5d1b amendment 004/freeze v5 already exists")
    parent = load_json(PARENT)
    parent_body = dict(parent)
    parent_sha = parent_body.pop("freeze_sha256")
    if canonical_sha256(parent_body) != parent_sha:
        raise ValueError("freeze v4 identity mismatch")
    for name, digest in parent["tool_hashes"].items():
        if sha256(HISTORY / name) != digest:
            raise ValueError(f"historical v4 tool identity mismatch: {name}")
    manifest = load_json(INVALIDATED_MANIFEST)
    if manifest["member_count"] != 17 or manifest["archive"]["sha256"] != sha256(INVALIDATED_ARCHIVE):
        raise ValueError("invalidated v4 certificate archive mismatch")
    if (ARTIFACTS / "count-feasibility-results-v1.json").exists():
        raise ValueError("v4 unexpectedly emitted a count aggregate")
    amendment = {
        "post_outcome_correction_amendment_schema_version": 1,
        "parent_freeze_sha256": parent_sha,
        "classification": "post-outcome aggregate-only missing-import correction",
        "scientific_contract_changed": False,
        "algorithm_implementation_changed": False,
        "tolerance_changed": False,
        "matrix_changed": False,
        "correction": "Import the repository ROOT constant used only while reading completed station certificates to form aggregate separate-horizon counts.",
        "trigger": "All 17 corrected v4 station certificates were written; aggregate construction then raised NameError because ROOT was not imported. No count aggregate, ordered path, terminal result, or decision was emitted.",
        "v4_outcome_exposure": {
            "count_certificate_files_written": 17,
            "count_aggregate_files_written": 0,
            "ordered_path_files_written": 0,
            "terminal_result_files_written": 0,
            "confirmation_objects_accessed": 0,
            "invalidated_certificate_archive": {
                "path": INVALIDATED_ARCHIVE.name,
                "bytes": INVALIDATED_ARCHIVE.stat().st_size,
                "sha256": sha256(INVALIDATED_ARCHIVE),
            },
            "invalidated_certificate_manifest": {
                "path": INVALIDATED_MANIFEST.name,
                "bytes": INVALIDATED_MANIFEST.stat().st_size,
                "sha256": sha256(INVALIDATED_MANIFEST),
            },
        },
        "historical_v4_tool_directory": "history/v4-tools",
        "historical_v4_tool_hashes": parent["tool_hashes"],
    }
    write_json(AMENDMENT_004, amendment)
    freeze = {
        "corrected_execution_freeze_schema_version": 5,
        "state": "FROZEN-AFTER-V4-CERTIFICATE-INVALIDATION-AND-BEFORE-CORRECTED-RERUN",
        "development_only": True,
        "root_prospective_freeze_sha256": parent["root_prospective_freeze_sha256"],
        "parent_freeze_sha256": parent_sha,
        "amendment_sha256": sha256(AMENDMENT_004),
        "evidence_lock_sha256": sha256(LOCK),
        "contract_sha256": sha256(CONTRACT),
        "incumbent_acceptance_fixture_results_sha256": parent["incumbent_acceptance_fixture_results_sha256"],
        "tool_hashes": {name: sha256(ARTIFACTS / name) for name in TOOLS},
        "count_matrix": parent["count_matrix"],
        "path_matrix": parent["path_matrix"],
        "expected_count_cells": parent["expected_count_cells"],
        "expected_path_cells_if_count_gate_passes": parent["expected_path_cells_if_count_gate_passes"],
        "diagnostic_freeze_sha256": parent["diagnostic_freeze_sha256"],
        "inherited_diagnostic_results_sha256": parent["inherited_diagnostic_results_sha256"],
        "corrected_count_aggregate_files_existing_at_v5_freeze": [],
        "selection_rule": parent["selection_rule"],
        "confirmation_objects_in_scope": 0,
    }
    freeze["freeze_sha256"] = canonical_sha256(freeze)
    write_json(FREEZE_V5, freeze)
    EXPOSURE.write_text(
        "# A5d1b Exposure Ledger\n\n"
        "Status: `CORRECTED-V5-FROZEN-ZERO-CONFIRMATION-EXPOSURE`\n\n"
        "- Confirmation objects accessed: **0**\n"
        "- Confirmation target values or scores accessed: **0**\n"
        "- Confirmation WEPP responses accessed: **0**\n"
        "- Public candidate/profile identifiers created: **0**\n"
        "- Production or accepted public surfaces changed: **0**\n\n"
        "The v1 freeze preceded every A5d1b result. Amendments 001/002 repaired null-safe optional metadata serialization before count results. Post-outcome amendment 003 invalidated v3 and corrected incumbent acceptance. All 17 v4 station certificates were then preserved and invalidated when aggregate-only code raised a missing-import NameError; amendment 004 changes no scientific calculation, algorithm, tolerance, or matrix.\n\n"
        f"The controlling v5 execution freeze identity is `{freeze['freeze_sha256']}`.\n",
        encoding="utf-8",
    )
    print(f"A5d1b corrected execution freeze v5: PASS ({freeze['freeze_sha256']})")


if __name__ == "__main__":
    main()
