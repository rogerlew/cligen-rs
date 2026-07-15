#!/usr/bin/env python3
"""Create the immutable A5d1b input lock and pre-outcome freeze."""

from __future__ import annotations

import platform
import subprocess
import sys

import numpy
import scipy
from jsonschema import Draft202012Validator

from a5d1b_common import (
    A5D1,
    A5D1_CONTRACT,
    A5D1_DECISION,
    A5D1_DETAILED_ARCHIVE,
    A5D1_DETAILED_MANIFEST,
    A5D1_FEATURE_MANIFEST,
    A5D1_FREEZE,
    A5D1_LIBRARY_MANIFEST,
    A5D1_MARGINAL,
    A5D1_PATH_RESULTS,
    ARTIFACTS,
    CONTRACT,
    CONTRACT_SCHEMA,
    COUNT_RESULTS,
    DIAGNOSTIC_RESULTS,
    FREEZE,
    LOCK,
    PATH_RESULTS,
    ROOT,
    canonical_sha256,
    certificate_path,
    feature_path,
    identity,
    load_json,
    sha256,
    station_ids,
    write_json,
)


EXPOSURE = ARTIFACTS / "exposure-ledger.md"
FIXTURES = ARTIFACTS / "synthetic-fixtures-v1.json"
FIXTURE_RESULTS = ARTIFACTS / "synthetic-fixture-results-v1.json"
ADVISORY = ARTIFACTS / "inherited-a5d1-hash-advisory.md"
TOOLS = [
    "a5d1b_common.py",
    "freeze-a5d1b.py",
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
        raise SystemExit("usage: freeze-a5d1b.py")
    if FREEZE.exists() or LOCK.exists():
        raise ValueError("A5d1b freeze/lock already exists; immutable overwrite refused")
    contract = load_json(CONTRACT)
    schema = load_json(CONTRACT_SCHEMA)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(contract)
    if not isinstance(contract, dict):
        raise ValueError("contract is not an object")
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    if source_commit != contract["source_commit"]:
        raise ValueError("contract source commit does not match HEAD")
    inherited = {
        "a5d1_contract_sha256": sha256(A5D1_CONTRACT),
        "a5d1_decision_sha256": sha256(A5D1_DECISION),
        "a5d1_detailed_archive_sha256": sha256(A5D1_DETAILED_ARCHIVE),
        "a5d1_feature_manifest_sha256": sha256(A5D1_FEATURE_MANIFEST),
        "a5d1_freeze_sha256": load_json(A5D1_FREEZE)["freeze_sha256"],
        "a5d1_library_manifest_sha256": sha256(A5D1_LIBRARY_MANIFEST),
        "a5d1_marginal_results_sha256": sha256(A5D1_MARGINAL),
        "a5d1_path_results_sha256": sha256(A5D1_PATH_RESULTS),
    }
    if inherited != contract["inherited"]:
        raise ValueError("A5d1 inherited identities do not match the prospective contract")
    feature_manifest = load_json(A5D1_FEATURE_MANIFEST)
    marginal = load_json(A5D1_MARGINAL)
    libraries = load_json(A5D1_LIBRARY_MANIFEST)
    feature_index = {row["station_id"]: row for row in feature_manifest["records"]}
    marginal_index = {row["station_id"]: row for row in marginal["records"] if row["pool_size"] == 256}
    library_index = {row["station_id"]: row for row in libraries["records"]}
    station_inputs = []
    for station_id in station_ids():
        feature = feature_path(station_id)
        certificate = certificate_path(station_id)
        cli = ROOT / library_index[station_id]["cli"]["path"]
        if sha256(feature) != feature_index[station_id]["sha256"]:
            raise ValueError(f"feature manifest mismatch: {station_id}")
        if sha256(certificate) != marginal_index[station_id]["certificate"]["sha256"]:
            raise ValueError(f"marginal certificate mismatch: {station_id}")
        if sha256(cli) != library_index[station_id]["cli"]["sha256"]:
            raise ValueError(f"library climate mismatch: {station_id}")
        station_inputs.append(
            {
                "station_id": station_id,
                "role": "exposed_development_only",
                "feature": identity(feature),
                "marginal_certificate": identity(certificate),
                "faithful_off_library": identity(cli),
            }
        )
    authorities = [
        ROOT / "AGENTS.md",
        ROOT / "docs/decisions/0001-source-code-authority-port.md",
        ROOT / "docs/decisions/0002-quality-metrics-authority.md",
        ROOT / "docs/decisions/0004-a5b-interannual-no-promotion.md",
        ROOT / "docs/standards/rust-scientific-coding-standard.md",
        ROOT / "docs/standards/scientific-report-standard.md",
        ROOT / "docs/standards/scientific-report-authoring-protocol.md",
        A5D1_CONTRACT,
        A5D1 / "selector-feasibility-contract-v4.schema.json",
        A5D1 / "evidence-lock-inputs-v6.json",
        A5D1_FREEZE,
        A5D1_LIBRARY_MANIFEST,
        A5D1_FEATURE_MANIFEST,
        A5D1_MARGINAL,
        A5D1_PATH_RESULTS,
        A5D1_DETAILED_MANIFEST,
        A5D1_DETAILED_ARCHIVE,
        A5D1 / "physical-row-identity-audit-v1.json",
        A5D1 / "selector-feasibility-results-v1.json",
        A5D1_DECISION,
        A5D1 / "closure-evidence-v1.json",
        ADVISORY,
    ]
    outcome_candidates = [
        DIAGNOSTIC_RESULTS,
        COUNT_RESULTS,
        PATH_RESULTS,
        ARTIFACTS / "detailed-evidence-v1.tar.gz",
        ARTIFACTS / "detailed-evidence-manifest-v1.json",
        ARTIFACTS / "a5d1b-results-v1.json",
        ARTIFACTS / "a5d1b-decision-v1.json",
    ]
    existing = [str(path.relative_to(ROOT)) for path in outcome_candidates if path.exists()]
    if existing:
        raise ValueError(f"A5d1b actual outcome exists before freeze: {existing}")
    lock = {
        "evidence_lock_schema_version": 1,
        "development_only": True,
        "source_commit": source_commit,
        "authority_inputs": [identity(path) for path in authorities],
        "contract": identity(CONTRACT),
        "contract_schema": identity(CONTRACT_SCHEMA),
        "synthetic_fixtures": identity(FIXTURES),
        "synthetic_fixture_results": identity(FIXTURE_RESULTS),
        "station_count": len(station_inputs),
        "stations": station_inputs,
        "tooling": [identity(ARTIFACTS / name) for name in TOOLS],
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": numpy.__version__,
            "scipy": scipy.__version__,
            "solver": "scipy.optimize.milp using HiGHS",
        },
        "exposure": {
            "confirmation_objects_accessed": 0,
            "confirmation_target_values_accessed": 0,
            "confirmation_wepp_responses_accessed": 0,
            "allowed": [
                "accepted repository authorities",
                "17 exposed A5a/A5b development stations",
                "accepted A5d1 evidence and ignored hash-reconciled working outputs",
                "outcome-independent A5d1b synthetic fixtures",
            ],
        },
        "production_source_changes": 0,
        "public_surface_changes": 0,
        "predecessor_report_authority": "contextual_only_due_to_dispositioned_review_hash_staleness",
    }
    write_json(LOCK, lock)
    count_matrix = [{"station_id": station_id, "pool_size": 256} for station_id in station_ids()]
    path_matrix = [
        {"station_id": station_id, "pool_size": 256, "algorithm": contract["algorithm"]["ordering_id"], "path_seed": seed}
        for station_id in station_ids()
        for seed in contract["matrix"]["path_seeds"]
    ]
    freeze = {
        "pre_outcome_freeze_schema_version": 1,
        "state": "FROZEN-BEFORE-A5D1B-ACTUAL-OUTCOMES-AFTER-A5D1-EXPOSURE",
        "development_only": True,
        "source_commit": source_commit,
        "evidence_lock_sha256": sha256(LOCK),
        "contract_sha256": sha256(CONTRACT),
        "contract_schema_sha256": sha256(CONTRACT_SCHEMA),
        "synthetic_fixture_results_sha256": sha256(FIXTURE_RESULTS),
        "tool_hashes": {name: sha256(ARTIFACTS / name) for name in TOOLS},
        "count_matrix": count_matrix,
        "path_matrix": path_matrix,
        "expected_count_cells": len(count_matrix),
        "expected_path_cells_if_count_gate_passes": len(path_matrix),
        "inherited_outcome_access": {
            "a5d1_pool_256_path_cells": 153,
            "a5d1_terminal_status": "EXECUTED-HOLD-PATH-INFEASIBILITY",
            "role": "exposed development evidence used to design A5d1b prospectively",
        },
        "a5d1b_outcome_files_existing_at_freeze": existing,
        "selection_rule": contract["selection_rule"],
        "confirmation_objects_in_scope": 0,
    }
    freeze["freeze_sha256"] = canonical_sha256(freeze)
    write_json(FREEZE, freeze)
    EXPOSURE.write_text(
        "# A5d1b Exposure Ledger\n\n"
        "Status: `FROZEN-PRE-OUTCOME-ZERO-CONFIRMATION-EXPOSURE`\n\n"
        "Allowed evidence is limited to accepted repository authorities, the 17 already exposed A5a/A5b development stations, accepted A5d1 evidence, hash-reconciled ignored A5d1 working outputs, and synthetic fixtures.\n\n"
        "- Confirmation objects accessed: **0**\n"
        "- Confirmation target values or scores accessed: **0**\n"
        "- Confirmation WEPP responses accessed: **0**\n"
        "- Public candidate/profile identifiers created: **0**\n"
        "- Production or accepted public surfaces changed: **0**\n\n"
        f"The machine allowlist is in `evidence-lock-inputs-v1.json`; the immutable pre-outcome identity is `{freeze['freeze_sha256']}`.\n",
        encoding="utf-8",
    )
    print(f"A5d1b pre-outcome freeze: PASS ({len(count_matrix)} count; {len(path_matrix)} conditional path; {freeze['freeze_sha256']})")


if __name__ == "__main__":
    main()

