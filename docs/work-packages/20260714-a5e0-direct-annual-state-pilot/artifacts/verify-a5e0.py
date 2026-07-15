#!/usr/bin/env python3
"""Seal and verify the retained A5e0 exploratory campaign evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys
from typing import Any, Iterator

from jsonschema import Draft202012Validator


sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent.parent
ARTIFACTS = PACKAGE / "artifacts"
MATRIX = ROOT / "target/a5e0/matrix-index-v1.json"
CAMPAIGN = ARTIFACTS / "a5e0-campaign-evidence-v1.json"
SOURCE_MANIFEST = ARTIFACTS / "a5e0-implementation-tree-v1.json"
COEFFICIENTS = ARTIFACTS / "a5e0-coefficients-v1.json"
FEASIBILITY = ARTIFACTS / "a5e0-feasibility-v1.json"
ANALYSIS = ARTIFACTS / "a5e0-analysis-v1.json"
DESCRIPTOR_AUDIT = ARTIFACTS / "a5e0-descriptor-rule-audit-v1.json"
COEFFICIENT_SCHEMA = ROOT / "docs/specifications/a5e0-coefficients-v1.schema.json"
CAMPAIGN_SCHEMA = ROOT / "docs/specifications/a5e0-campaign-evidence-v1.schema.json"
PILOT_SPEC = ROOT / "docs/specifications/SPEC-A5E0-PILOT.md"
SOURCE_COMMIT = "27e5e7754bdfafcca649a71d0f5576910433d0d3"
STATIONS = ("ca042319", "co051660", "ms227840")
ARMS = ("research_baseline", "candidate")


class EvidenceError(RuntimeError):
    """A retained A5e0 evidence invariant failed."""


def strict_json_bytes(raw: bytes, label: str) -> Any:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise EvidenceError(f"duplicate key {key!r} in {label}")
            result[key] = value
        return result

    try:
        return json.loads(
            raw,
            object_pairs_hook=pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                EvidenceError(f"nonfinite token {token!r} in {label}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceError(f"invalid JSON in {label}: {error}") from error


def strict_json(path: Path) -> Any:
    return strict_json_bytes(path.read_bytes(), str(path))


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(path),
        "bytes": path.stat().st_size,
    }


def resolve_artifact(value: dict[str, Any]) -> Path:
    path = ROOT / value["path"]
    if not path.is_file():
        raise EvidenceError(f"missing artifact {value['path']}")
    if path.stat().st_size != value["bytes"]:
        raise EvidenceError(f"byte count mismatch for {value['path']}")
    if sha256(path) != value["sha256"]:
        raise EvidenceError(f"SHA-256 mismatch for {value['path']}")
    return path


def artifacts_in(value: Any) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        if set(value) == {"path", "sha256", "bytes"}:
            yield value
        else:
            for child in value.values():
                yield from artifacts_in(child)
    elif isinstance(value, list):
        for child in value:
            yield from artifacts_in(child)


def validate_schema(value: Any, schema_path: Path) -> None:
    schema = strict_json(schema_path)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        location = "/".join(str(item) for item in first.absolute_path) or "<root>"
        raise EvidenceError(f"{schema_path.name} validation failed at {location}: {first.message}")


def implementation_paths() -> list[Path]:
    relative = (
        "Cargo.lock",
        "crates/cligen/src/a5e0.rs",
        "crates/cligen/src/lib.rs",
        "crates/cligen/src/modes.rs",
        "crates/cligen/src/rng.rs",
        "crates/cligen/examples/a5e0_runner.rs",
        "docs/specifications/SPEC-A5E0-PILOT.md",
        "docs/specifications/a5e0-coefficients-v1.schema.json",
        "docs/specifications/a5e0-campaign-evidence-v1.schema.json",
        "docs/work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/fit-a5e0.py",
        "docs/work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/run-a5e0-matrix.py",
        "docs/work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/analyze-a5e0.py",
        "docs/work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/audit-a5e0-descriptors.py",
        "docs/work-packages/20260714-a5e0-direct-annual-state-pilot/artifacts/verify-a5e0.py",
    )
    paths = [ROOT / item for item in relative]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise EvidenceError(f"implementation tree is missing: {missing}")
    return paths


def write_source_manifest() -> None:
    value = {
        "manifest_schema": "a5e0_implementation_tree_v1",
        "base_commit": SOURCE_COMMIT,
        "implementation_commit": None,
        "status": "post_output_identity_snapshot",
        "prospective_freeze_demonstrated": False,
        "files": [artifact(path) for path in implementation_paths()],
    }
    SOURCE_MANIFEST.write_bytes(canonical_bytes(value))


def conformance_artifacts() -> dict[str, Any]:
    directory = ROOT / "target/a5e0/conformance"
    return {
        "zero_bundle": artifact(directory / "all-zero-coefficients.json"),
        "baseline_cli": artifact(directory / "zero-research_baseline.cli"),
        "baseline_diagnostics": artifact(directory / "zero-research_baseline.diagnostics.json"),
        "candidate_cli": artifact(directory / "zero-candidate.cli"),
        "candidate_diagnostics": artifact(directory / "zero-candidate.diagnostics.json"),
    }


def campaign_runs(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in matrix["runs"]:
        products = row["products"]["100"]
        rows.append(
            {
                "run_id": row["run_id"],
                "station_id": row["station_id"],
                "arm": row["arm"],
                "replicate": row["replicate"],
                "master_seed": row["master_seed"],
                "faithful_segment": row["faithful_segment"],
                "faithful_raw_skip": row["faithful_raw_skip"],
                "years": 100,
                "annual_state_sha256": row["annual_state_sha256"],
                "cli": products["cli"],
                "quality": products["quality"],
                "diagnostics": products["diagnostics"],
            }
        )
    return rows


def write_campaign() -> None:
    matrix = strict_json(MATRIX)
    coefficients = strict_json(COEFFICIENTS)
    feasibility = strict_json(FEASIBILITY)
    source_manifest = artifact(SOURCE_MANIFEST)
    value = {
        "campaign_schema": "a5e0_campaign_evidence_v1",
        "status": "sealed",
        "identity": {
            "work_package": "20260714-a5e0-direct-annual-state-pilot",
            "research_profile": "a5e0_direct_annual_state_v1",
            "source_commit": SOURCE_COMMIT,
            "implementation_commit": None,
            "implementation_tree": source_manifest,
            "fit_recipe": "a5e0_direct_monthly_loading_fit_v1",
            "observed_snapshot": "daymet_v4r1_a5a17_fit1980_2009_noleap_v1",
        },
        "contracts": {
            "pilot_spec": artifact(PILOT_SPEC),
            "coefficient_schema": artifact(COEFFICIENT_SCHEMA),
            "campaign_schema": artifact(CAMPAIGN_SCHEMA),
        },
        "inputs": {
            "cargo_lock": artifact(ROOT / "Cargo.lock"),
            "executable": matrix["runner"],
            "quality_executable": matrix["cligen"],
            "fitter": artifact(ARTIFACTS / "fit-a5e0.py"),
            "analyzer": artifact(ARTIFACTS / "analyze-a5e0.py"),
            "verifier": artifact(Path(__file__).resolve()),
            "source_manifest": source_manifest,
            "matrix_index": artifact(MATRIX),
            "coefficient_bundle": artifact(COEFFICIENTS),
            "stations": matrix["station_inputs"],
            "daymet": [station["daymet"] for station in coefficients["stations"]],
        },
        "feasibility": {
            "status": feasibility["status"],
            "checks": [
                {"check": "coefficient_schema", "status": "PASS", "detail": "Strict schema validation passed."},
                {"check": "all_loadings_finite", "status": "PASS", "detail": "All 144 loadings are finite."},
                {"check": "occurrence_budget", "status": "PASS", "detail": "All joint-solve and probability limits passed."},
                {"check": "amount_budget", "status": "PASS", "detail": "All residual and reconstruction limits passed."},
                {"check": "temperature_budget", "status": "PASS", "detail": "All residual variance budgets passed."},
            ],
            "artifact": artifact(FEASIBILITY),
        },
        "matrix": {
            "stations": list(STATIONS),
            "arms": list(ARMS),
            "replicates": 8,
            "physical_run_years": 100,
            "nested_horizons": [30, 100],
            "expected_physical_runs": 48,
            "expected_cells": 96,
            "conformance": conformance_artifacts(),
        },
        "runs": campaign_runs(matrix),
        "hypotheses": {
            "h0": {"status": "PASS", "summary": "Exploratory analytic feasibility checks passed.", "artifact": artifact(FEASIBILITY)},
            "h1": {"status": "FAIL", "summary": "Exploratory intended-signal gate failed at 30 and 100 years.", "artifact": artifact(ANALYSIS)},
            "h2": {"status": "FAIL", "summary": "Exploratory preservation gate failed at 100 years.", "artifact": artifact(ANALYSIS)},
            "h3": {"status": "PASS", "summary": "Both descriptor-rule readings and other exploratory H3 guards passed.", "artifact": artifact(DESCRIPTOR_AUDIT)},
            "h4": {"status": "FAIL", "summary": "The exact prospective freeze and required predeclared engineering evidence were not demonstrated.", "artifact": None},
        },
        "decision": "EXECUTED-HOLD-PROSPECTIVE-BOUNDARY",
        "execution": {
            "started_utc": "2026-07-15T01:56:04Z",
            "completed_utc": "2026-07-15T01:56:16Z",
            "wall_time_seconds": matrix["wall_time_seconds"],
            "host": platform.node(),
            "rustc_version": subprocess.run(["rustc", "--version"], capture_output=True, text=True, check=True).stdout.strip(),
            "python_version": platform.python_version(),
            "failures": [
                "The named source commit does not contain the exact pilot specification, implementation, or analyzer.",
                "The exact prospective specification/analyzer hashes were not independently sealed before outcome access.",
                "The fitter did not follow the specification's stated math.fsum rule for all loading calculations.",
                "The runtime intake did not independently reconstruct occurrence and amount derived values.",
                "The typed-row prefix and conservative RNG-bound obligations were not demonstrated in their predeclared forms.",
            ],
        },
        "outputs": {
            "analysis": artifact(ANALYSIS),
            "descriptor_subfamily_audit": artifact(DESCRIPTOR_AUDIT),
        },
    }
    CAMPAIGN.write_bytes(canonical_bytes(value))


def verify_source_manifest(value: dict[str, Any]) -> None:
    if value.get("base_commit") != SOURCE_COMMIT or value.get("prospective_freeze_demonstrated") is not False:
        raise EvidenceError("implementation-tree disposition differs")
    paths = []
    for item in value.get("files", []):
        resolve_artifact(item)
        paths.append(item["path"])
    expected = [path.relative_to(ROOT).as_posix() for path in implementation_paths()]
    if paths != expected or len(paths) != len(set(paths)):
        raise EvidenceError("implementation-tree membership differs")


def verify_matrix(campaign: dict[str, Any], matrix: dict[str, Any]) -> None:
    runs = campaign["runs"]
    expected = [
        (station, arm, replicate)
        for station in STATIONS
        for arm in ARMS
        for replicate in range(1, 9)
    ]
    actual = [(row["station_id"], row["arm"], row["replicate"]) for row in runs]
    if actual != expected:
        raise EvidenceError("campaign run order or closure differs")
    if len(matrix["runs"]) != 48:
        raise EvidenceError("matrix index does not contain 48 runs")
    for row in runs:
        ordinal = STATIONS.index(row["station_id"])
        segment = 8 * ordinal + row["replicate"] - 1
        if row["faithful_segment"] != segment or row["faithful_raw_skip"] != segment * 500_000:
            raise EvidenceError(f"faithful partition mismatch in {row['run_id']}")
        diagnostics = strict_json(ROOT / row["diagnostics"]["path"])
        if diagnostics["faithful_segment"] != segment or max(diagnostics["actual_raw_updates"]) >= 500_000:
            raise EvidenceError(f"diagnostic partition mismatch in {row['run_id']}")
        if row["arm"] == "candidate":
            if row["annual_state_sha256"] is None or len(diagnostics["annual_states"]) != 100:
                raise EvidenceError(f"candidate annual-state mismatch in {row['run_id']}")
        elif row["annual_state_sha256"] is not None or diagnostics["annual_states"]:
            raise EvidenceError(f"baseline consumed extension state in {row['run_id']}")


def verify_campaign() -> None:
    coefficient = strict_json(COEFFICIENTS)
    validate_schema(coefficient, COEFFICIENT_SCHEMA)
    campaign = strict_json(CAMPAIGN)
    validate_schema(campaign, CAMPAIGN_SCHEMA)
    for item in artifacts_in(campaign):
        resolve_artifact(item)
    source = strict_json(SOURCE_MANIFEST)
    verify_source_manifest(source)
    matrix = strict_json(MATRIX)
    verify_matrix(campaign, matrix)
    analysis = strict_json(ANALYSIS)
    if analysis["identity"]["matrix_index_sha256"] != sha256(MATRIX):
        raise EvidenceError("analysis does not bind the matrix index")
    if analysis["climate_decision"] != "CLOSE-MECHANISM":
        raise EvidenceError("provisional climate mapping differs")
    if campaign["hypotheses"]["h4"]["status"] != "FAIL" or campaign["decision"] != "EXECUTED-HOLD-PROSPECTIVE-BOUNDARY":
        raise EvidenceError("terminal evidence disposition differs")


def self_test() -> None:
    try:
        strict_json_bytes(b'{"a":1,"a":2}', "duplicate fixture")
    except EvidenceError:
        pass
    else:
        raise EvidenceError("duplicate-key self-test did not fail")
    try:
        strict_json_bytes(b'{"a":NaN}', "nonfinite fixture")
    except EvidenceError:
        pass
    else:
        raise EvidenceError("nonfinite self-test did not fail")
    mutated = strict_json(CAMPAIGN)
    mutated["unknown"] = True
    try:
        validate_schema(mutated, CAMPAIGN_SCHEMA)
    except EvidenceError:
        pass
    else:
        raise EvidenceError("unknown-field schema self-test did not fail")
    altered = dict(mutated["inputs"]["cargo_lock"])
    altered["sha256"] = "0" * 64
    try:
        resolve_artifact(altered)
    except EvidenceError:
        pass
    else:
        raise EvidenceError("artifact-mutation self-test did not fail")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seal", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args()
    if arguments.seal:
        write_source_manifest()
        write_campaign()
    verify_campaign()
    if arguments.self_test:
        self_test()
    print("A5e0 evidence verification: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (EvidenceError, OSError, subprocess.CalledProcessError) as error:
        print(f"A5e0 evidence verification: FAIL: {error}", file=sys.stderr)
        raise SystemExit(1)
