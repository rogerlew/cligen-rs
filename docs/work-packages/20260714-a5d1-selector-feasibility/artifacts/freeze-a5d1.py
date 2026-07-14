#!/usr/bin/env python3
"""Create the immutable A5d1 input/exposure lock and pre-solver freeze."""

from __future__ import annotations

import gzip
import hashlib
import platform
import subprocess
import sys

import numpy
import scipy
from jsonschema import Draft202012Validator

from a5d1_common import (
    A5B_BUNDLES,
    CONTRACT,
    CORPUS_CONFIG,
    DAYMET_DIR,
    FREEZE,
    OBSERVED_TARGETS,
    PACKAGE,
    ROOT,
    canonical_sha256,
    load_json,
    relative,
    sha256,
    station_records,
    write_json,
)


INPUT_LOCK = PACKAGE / "evidence-lock-inputs-v6.json"
EXPOSURE = PACKAGE / "exposure-ledger-v6.md"
SCHEMA = PACKAGE / "selector-feasibility-contract-v4.schema.json"
FIXTURES = PACKAGE / "synthetic-feasibility-fixtures-v1.json"
AMENDMENT = PACKAGE / "pre-solver-freeze-amendment-005.json"
BINARY = ROOT / "target/release/cligen"
TOOLS = [
    "a5d1_common.py",
    "freeze-a5d1.py",
    "build-development-libraries.py",
    "build-year-features.py",
    "solve-selector-feasibility.py",
    "run-path-feasibility.py",
    "run-synthetic-fixtures.py",
    "archive-detailed-evidence.py",
    "finalize-a5d1.py",
    "verify-a5d1-package.py",
    "verify-physical-row-identity.py",
]


def identity(path) -> dict:
    return {"path": relative(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def decompressed_sha256(path) -> str:
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    if len(sys.argv) != 1:
        raise SystemExit("usage: freeze-a5d1.py")
    if FREEZE.exists():
        raise ValueError("pre-solver freeze already exists; immutable overwrite refused")
    contract = load_json(CONTRACT)
    schema = load_json(SCHEMA)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(contract)
    stations = station_records()
    station_inputs = []
    for station in stations:
        station_id = station["station_id"]
        daymet = DAYMET_DIR / f"{station_id}.csv.gz"
        bundle = A5B_BUNDLES / f"{station_id}.a5b.station.json"
        value = load_json(bundle)
        fourier = next(item for item in value["extensions"] if item["candidate_id"] == "fourier_eof")
        if decompressed_sha256(daymet) != station["daymet_source_sha256"]:
            raise ValueError(f"Daymet identity mismatch: {station_id}")
        station_inputs.append(
            {
                "station_id": station_id,
                "role": "exposed_development_only",
                "par_sha256": station["par_sha256"],
                "daymet": identity(daymet)
                | {"decompressed_sha256": station["daymet_source_sha256"]},
                "bundle": identity(bundle),
                "fourier_eof": {
                    "fit_identity_sha256": fourier["fit_identity_sha256"],
                    "payload_sha256": fourier["diagnostics"]["payload_sha256"],
                },
            }
        )
    authorities = [
        ROOT / "docs/decisions/0001-source-code-authority-port.md",
        ROOT / "docs/decisions/0002-quality-metrics-authority.md",
        ROOT / "docs/decisions/0004-a5b-interannual-no-promotion.md",
        ROOT / "docs/standards/rust-scientific-coding-standard.md",
        ROOT / "docs/work-packages/20260714-a5c-interannual-profile-adjudication/artifacts/a5c-decision-v1.json",
        ROOT / "docs/work-packages/20260714-a5c-interannual-profile-adjudication/artifacts/evidence-lock-v1.json",
        ROOT / "docs/work-packages/20260714-a5d0-successor-feasibility-calibration/artifacts/a5d0-decision-v1.json",
        ROOT / "docs/work-packages/20260714-a5d0-successor-feasibility-calibration/artifacts/closure-evidence-v1.json",
        CORPUS_CONFIG,
        OBSERVED_TARGETS,
        AMENDMENT,
    ]
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    lock = {
        "evidence_lock_schema_version": 1,
        "development_only": True,
        "source_commit": source_commit,
        "authority_inputs": [identity(path) for path in authorities],
        "station_count": len(station_inputs),
        "stations": station_inputs,
        "generator_binary": identity(BINARY),
        "tooling": [identity(PACKAGE / name) for name in TOOLS],
        "contract": identity(CONTRACT),
        "contract_schema": identity(SCHEMA),
        "fixtures": identity(FIXTURES),
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": numpy.__version__,
            "scipy": scipy.__version__,
            "solver": "scipy.optimize.linprog(method=highs)",
        },
        "exposure": {
            "confirmation_objects_accessed": 0,
            "confirmation_target_values_accessed": 0,
            "confirmation_wepp_responses_accessed": 0,
            "allowlist": [
                "accepted authorities and public generator inputs",
                "17 A5a/A5b exposed station and Daymet development records",
                "A5b Fourier/EOF development identities",
                "regenerated faithful-off libraries",
                "A5d1 synthetic fixtures",
            ],
        },
        "public_surface_changes": 0,
        "production_source_changes": 0,
    }
    write_json(INPUT_LOCK, lock)
    matrix = []
    for station in stations:
        for pool_size in contract["pool_sizes"]:
            for realization in contract["library_realizations"]:
                for algorithm in contract["algorithms"]:
                    for seed in contract["path"]["path_seeds"]:
                        matrix.append(
                            {
                                "station_id": station["station_id"],
                                "pool_size": pool_size,
                                "library_realization": realization["id"],
                                "algorithm": algorithm,
                                "path_seed": seed,
                            }
                        )
    outcome_candidates = [
        PACKAGE / "development-library-manifest-v1.json",
        PACKAGE / "year-feature-manifest-v1.json",
        PACKAGE / "selector-feasibility-results-v1.json",
        PACKAGE / "a5d1-decision-v1.json",
        ROOT / "target/a5d1-selector-feasibility/marginal-results-v1.json",
        ROOT / "target/a5d1-selector-feasibility/path-results-v1.json",
    ]
    existing_outcomes = [relative(path) for path in outcome_candidates if path.exists()]
    if existing_outcomes:
        raise ValueError(f"v6 outcome files exist before freeze: {existing_outcomes}")
    freeze = {
        "pre_solver_freeze_schema_version": 6,
        "state": "FROZEN-BEFORE-V6-OUTCOMES-AFTER-INVALIDATED-V2-V3-V4-AND-V5",
        "development_only": True,
        "evidence_lock_sha256": sha256(INPUT_LOCK),
        "contract_sha256": sha256(CONTRACT),
        "contract_schema_sha256": sha256(SCHEMA),
        "fixture_sha256": sha256(FIXTURES),
        "amendment_sha256": sha256(AMENDMENT),
        "tool_hashes": {name: sha256(PACKAGE / name) for name in TOOLS},
        "pool_sizes": contract["pool_sizes"],
        "library_realizations": contract["library_realizations"],
        "algorithms": contract["algorithms"],
        "path_seeds": contract["path"]["path_seeds"],
        "expected_unique_cells": len(matrix),
        "matrix": matrix,
        "selection_rule": contract["selection_rule"],
        "outcome_files_existing_at_freeze": existing_outcomes,
        "prior_invalidated_outcomes": [
            {
                "freeze_sha256": "351b46ff2e0d2d92c9424ff6412822ae56911cca94b3a0b8e71dc8159b39500a",
                "version": "v2",
                "disposition": "invalidated uniform-reference denominator implementation defect"
            },
            {
                "freeze_sha256": "61e557154cd3e4e4b6ee31b068c0e7b61e9df04d2880d7cd25d27dd2e83d45fc",
                "version": "v3",
                "disposition": "invalidated independent-review scientific and finite-path implementation defects"
            },
            {
                "freeze_sha256": "9b408216af554a1f2b773e2ffd1560c731a245de1cf1e155b89b1dcbaaf03aa7",
                "version": "v4",
                "disposition": "invalidated omitted realized January 1 fitted-surface transition replay"
            },
            {
                "freeze_sha256": "726c2c761d38f1fd3399de9e64d171a36921e00da09c0ae3824f4e4e6cbe6d10",
                "version": "v5",
                "disposition": "stopped partial execution; invalidated overrestrictive boundary-subset fitted-surface gate"
            }
        ],
        "confirmation_objects_in_scope": 0,
    }
    freeze["freeze_sha256"] = canonical_sha256(freeze)
    write_json(FREEZE, freeze)
    EXPOSURE.write_text(
        "# A5d1 Exposure Ledger\n\n"
        "Status: `CLOSED-ZERO-CONFIRMATION-EXPOSURE`\n\n"
        "A5d1 used only the 17 previously exposed A5a/A5b development stations, their accepted station parameters, exposed Daymet 1980-2009 fit records, A5b Fourier/EOF identities, regenerated faithful-off libraries, and synthetic fixtures.\n\n"
        "- Confirmation objects accessed: **0**\n"
        "- Confirmation target values or scores accessed: **0**\n"
        "- Confirmation WEPP responses accessed: **0**\n"
        "- Public candidate/profile identifiers created: **0**\n"
        "- Production or accepted public surfaces changed: **0**\n\n"
        f"The complete allowlist and per-station hashes are machine-bound in `evidence-lock-inputs-v6.json`; the immutable v6 pre-result identity is `{freeze['freeze_sha256']}`. Prior v2/v3/v4/v5 development outcomes were invalidated and are disclosed in the freeze; no confirmation evidence was involved.\n",
        encoding="utf-8",
    )
    print(f"A5d1 pre-solver freeze: PASS ({len(matrix)} cells; {freeze['freeze_sha256']})")


if __name__ == "__main__":
    main()
