#!/usr/bin/env python3
"""Exercise every A9b command boundary with synthetic temporary inputs."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from research.a9_harness.canonical import sha256_bytes, write_canonical
from research.a9_harness.cli import (
    command_calibrate,
    command_confirm,
    command_evaluate,
    command_fit,
    command_optimize,
    command_validate,
    command_verify_log,
)
from research.a9_harness.fixtures import _role_manifest, _synthetic_fit_artifact


def namespace(**values: object) -> argparse.Namespace:
    return argparse.Namespace(**values)


def main() -> int:
    role_schema = ROOT / "docs/specifications/a9-data-role-manifest-v1.schema.json"
    objective_schema = ROOT / "docs/specifications/a9-objective-registry-v1.schema.json"
    objective_registry = ROOT / "docs/work-packages/20260715-a9a-successor-family-foundation/artifacts/objective-registry-v1.json"
    results: dict[str, object] = {}
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        role_path = directory / "roles.json"
        write_canonical(role_path, _role_manifest())
        results["validate"] = command_validate(
            namespace(artifact=str(objective_registry), schema=str(objective_schema), kind="objective")
        )

        exposures = directory / "exposures.json"
        write_canonical(
            exposures,
            {
                "synthetic_only": True,
                "effective_exposures": {
                    "wet_days": 100,
                    "dry_days": 100,
                    "adjacent_wet_pairs": 25,
                    "events": 50,
                },
                "fit_artifact_template": _synthetic_fit_artifact(),
            },
        )
        fit_output = directory / "fit.json"
        results["fit"] = command_fit(
            namespace(
                role_manifest=str(role_path),
                role_schema=str(role_schema),
                fit_schema=str(ROOT / "docs/specifications/a9-fit-artifact-v1.schema.json"),
                candidate_plugin="alternating_renewal_marked_v1",
                exposures=str(exposures),
                output=str(fit_output),
            )
        )

        evaluation_input = directory / "evaluation.json"
        write_canonical(evaluation_input, {"synthetic_only": True, "objectives": {"distance": 0.5}})
        results["evaluate"] = command_evaluate(
            namespace(
                role_manifest=str(role_path),
                role_schema=str(role_schema),
                role="development",
                input=str(evaluation_input),
                output=str(directory / "evaluation-output.json"),
            )
        )

        proposals = directory / "proposals.json"
        write_canonical(
            proposals,
            {
                "synthetic_only": True,
                "proposals": [
                    {"hard_feasible": True, "objectives": {"m1": 1.0, "m2": 2.0}},
                    {"hard_feasible": True, "objectives": {"m1": 2.0, "m2": 1.0}},
                    {"hard_feasible": False, "failed_constraints": ["support"]},
                ],
            },
        )
        log_directory = directory / "attempt-log"
        results["optimize"] = command_optimize(
            namespace(
                role_manifest=str(role_path),
                role_schema=str(role_schema),
                proposals=str(proposals),
                log_directory=str(log_directory),
                evaluations=3,
                wall_seconds=10.0,
                memory_bytes=1024 * 1024,
                retained_bytes=1024 * 1024,
                workers=1,
            )
        )
        results["verify-log"] = command_verify_log(namespace(log_directory=str(log_directory)))

        replicate_path = directory / "replicates.json"
        replicates = [
            {
                "aggregate:30": [index / 10000.0, (100 - index) / 10000.0],
                "aggregate:100": [index / 20000.0, (100 - index) / 20000.0],
            }
            for index in range(100)
        ]
        write_canonical(
            replicate_path,
            {
                "synthetic_only": True,
                "replicates": replicates,
                "floors": {"aggregate:30": 0.001, "aggregate:100": 0.001},
            },
        )
        results["calibrate-gates"] = command_calibrate(
            namespace(
                role_manifest=str(role_path),
                role_schema=str(role_schema),
                replicates=str(replicate_path),
                output=str(directory / "thresholds.json"),
            )
        )

        freeze_hash = sha256_bytes(b"command-surface-synthetic-freeze")
        sealed_path = directory / "sealed.json"
        write_canonical(
            sealed_path,
            _role_manifest(
                "sealed",
                sha256_bytes(b"command-surface-synthetic-object"),
                sha256_bytes(b"command-surface-synthetic-logical"),
                freeze_hash,
            ),
        )
        results["confirm"] = command_confirm(
            namespace(
                sealed_freeze=str(sealed_path),
                role_schema=str(role_schema),
                freeze_sha256=freeze_hash,
                actor="a9b-command-fixture",
                access_log_directory=str(directory / "access-log"),
            )
        )

    fixture_results = json.loads((ARTIFACTS / "generated/fixture-results-v1.json").read_text(encoding="utf-8"))
    results["run-fixtures"] = {
        "status": fixture_results["status"],
        "fixtures_passed": fixture_results["fixtures_passed"],
        "artifact_sha256": sha256_bytes((ARTIFACTS / "generated/fixture-results-v1.json").read_bytes()),
    }
    record = {
        "schema_version": 1,
        "surface_id": "a9b-command-surface-v1",
        "synthetic_only": True,
        "observed_target_access": False,
        "commands": results,
    }
    write_canonical(ARTIFACTS / "generated/command-surface-v1.json", record)
    print(f"exercised {len(results)} commands")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
