#!/usr/bin/env python3
"""Verify the closed A9c availability-hold package."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parents[1]
ARTIFACTS = PACKAGE / "artifacts"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run(*command: str) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    predecessor = load(ARTIFACTS / "predecessor-manifest-v1.json")
    require(predecessor["predecessor_terminal"] == "HARNESS-READY-A9C", "predecessor terminal")
    for record in predecessor["files"]:
        path = ROOT / record["path"]
        require(path.stat().st_size == record["bytes"] and sha(path) == record["sha256"], f"predecessor: {path}")

    run(sys.executable, "-m", "research.a9c.data", "verify")
    run(
        sys.executable,
        "-m",
        "research.a9_harness",
        "validate",
        str(ARTIFACTS / "data-role-manifest-v1.json"),
        "--schema",
        str(ROOT / "docs/specifications/a9-data-role-manifest-v1.schema.json"),
        "--kind",
        "role",
    )
    run(sys.executable, "-m", "research.a9c.nulls", "verify")

    inventory = load(ARTIFACTS / "fit-attempt-inventory-v1.json")
    require(inventory["candidate_development_scores_accessed"] is False, "candidate score access")
    require(inventory["complete_fit_count"] == 5, "fit count")
    for record in inventory["complete_fit_artifacts"]:
        path = ROOT / record["path"]
        require(sha(path) == record["sha256"], f"fit hash: {path}")
        run(
            sys.executable,
            "-m",
            "research.a9_harness",
            "validate",
            str(path),
            "--schema",
            str(ROOT / "docs/specifications/a9-fit-artifact-v1.schema.json"),
            "--kind",
            "fit",
        )

    availability = load(ARTIFACTS / "gate-calibration-availability-v1.json")
    require(availability["terminal"] == "HOLD-A9C-GATE-CALIBRATION", "terminal")
    require(availability["failure_count"] == 3, "failure count")
    failed = {(row["objective_id"], row["stratum"], row["available_stations"], row["minimum_required"]) for row in availability["failed_cells"]}
    require(
        failed
        == {
            ("storm_time_to_peak", "hot_arid", 0, 2),
            ("storm_peak_ratio", "hot_arid", 0, 2),
            ("storm_joint_dependence", "hot_arid", 0, 2),
        },
        "failed availability cells",
    )
    require(availability["selection_executed"] is False, "selection executed")
    require(availability["confirmation_series_accessed"] is False, "confirmation access")

    confirmation = load(
        ROOT
        / "docs/work-packages/20260715-a9a-successor-family-foundation/artifacts/confirmation-metadata-selection-v1.json"
    )
    forbidden = {row["station_id"] for row in confirmation["stations"]}
    access = [json.loads(line) for line in (ARTIFACTS / "observed-access-log-v1.ndjson").read_text().splitlines()]
    require(len(access) == 180, "access ledger length")
    require(not forbidden & {row["station_id"] for row in access}, "confirmation station in access ledger")

    implementation = load(ARTIFACTS / "implementation-manifest-v1.json")
    for record in implementation["files"]:
        path = ROOT / record["path"]
        require(path.stat().st_size == record["bytes"] and sha(path) == record["sha256"], f"implementation: {path}")
    require(implementation["production_runtime_changed"] is False, "runtime change")

    run(
        sys.executable,
        "docs/reports/verify-report.py",
        "docs/reports/a9c-observed-development-availability-report.manifest.json",
    )
    require("Status: `EXECUTED-HOLD-GATE-CALIBRATION`" in (PACKAGE / "package.md").read_text(), "package status")
    require("HOLD-A9C-GATE-CALIBRATION" in (ROOT / "docs/ROADMAP.md").read_text(), "roadmap terminal")
    require(not subprocess.run(["git", "diff", "--quiet", "--", "crates", "reference/cligen532"], cwd=ROOT).returncode, "production/reference diff")

    large = [path for path in ARTIFACTS.rglob("*") if path.is_file() and path.stat().st_size >= 10 * 1024 * 1024]
    for path in large:
        attribute = subprocess.check_output(["git", "check-attr", "filter", "--", str(path.relative_to(ROOT))], cwd=ROOT, text=True)
        require(attribute.rstrip().endswith(": lfs"), f"large file not LFS: {path}")
    print(
        "PASS: predecessor; 64 observed objects; 180 source accesses; 7000 null replicates; "
        "5 fits; 3-cell mandatory availability hold; zero confirmation/runtime access"
    )


if __name__ == "__main__":
    main()
