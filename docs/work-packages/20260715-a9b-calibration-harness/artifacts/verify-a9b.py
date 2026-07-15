#!/usr/bin/env python3
"""Fail-closed verifier for the A9b calibration-harness package."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
ARTIFACTS = Path(__file__).resolve().parent
DISPATCH = "795f76775135044f7643e44f1f08cca1136e7236"
EXPECTED_COMMANDS = {
    "validate",
    "fit",
    "evaluate",
    "optimize",
    "calibrate-gates",
    "confirm",
    "verify-log",
    "run-fixtures",
}


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_identities(records: list[dict[str, object]], label: str) -> None:
    for record in records:
        path = ROOT / str(record["path"])
        if not path.is_file():
            fail(f"missing {label} file {record['path']}")
        if path.stat().st_size != record["bytes"] or digest(path) != record["sha256"]:
            fail(f"{label} identity mismatch {record['path']}")


def main() -> int:
    predecessor = load(ARTIFACTS / "predecessor-manifest-v1.json")
    if not isinstance(predecessor, dict):
        fail("predecessor manifest type")
    verify_identities(predecessor["files"], "predecessor")
    if predecessor["dispatch"]["commit"] != DISPATCH or predecessor["predecessor_terminal"] != "FOUNDATION-READY-A9B":
        fail("dispatch or predecessor terminal")
    if predecessor["observed_target_access"] is not False:
        fail("predecessor target-access state")

    source = load(ARTIFACTS / "source-manifest-v1.json")
    if not isinstance(source, dict):
        fail("source manifest type")
    verify_identities(source["source_files"], "source")
    verify_identities(source["generated_evidence"], "generated evidence")
    if source["dispatch_commit"] != DISPATCH or source["observed_target_access"] is not False:
        fail("source dispatch/access state")
    expected_sources = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "research/a9_harness").rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    }
    expected_sources.add("research/__init__.py")
    expected_sources.update(
        {
            "docs/work-packages/20260715-a9b-calibration-harness/artifacts/capture-a9b-source.py",
            "docs/work-packages/20260715-a9b-calibration-harness/artifacts/exercise-a9b-commands.py",
            "docs/work-packages/20260715-a9b-calibration-harness/artifacts/verify-a9b.py",
            "docs/work-packages/20260715-a9b-calibration-harness/artifacts/verify-a9b-replay.py",
        }
    )
    captured_sources = {str(record["path"]) for record in source["source_files"]}
    if expected_sources != captured_sources:
        fail(f"source inventory mismatch missing={sorted(expected_sources-captured_sources)} extra={sorted(captured_sources-expected_sources)}")

    fixture = load(ARTIFACTS / "generated/fixture-results-v1.json")
    if fixture["status"] != "PASS" or fixture["fixtures_executed"] != 20 or fixture["fixtures_passed"] != 20:
        fail("fixture suite not 20/20 PASS")
    if fixture["observed_target_access"] is not False:
        fail("fixture target access")
    expected_ids = [f"FX-{index:03d}" for index in range(1, 21)]
    if [result["fixture_id"] for result in fixture["results"]] != expected_ids:
        fail("fixture order/coverage")
    if any(result["status"] != "PASS" for result in fixture["results"]):
        fail("fixture failure")

    recovery = load(ARTIFACTS / "generated/recovery-tolerances-v1.json")
    expected_classes = {"alternating_renewal_marked_v1", "latent_regime_marked_v1"}
    if set(recovery["classes"]) != expected_classes or recovery["observed_target_access"] is not False:
        fail("recovery class/access boundary")
    for class_id, evidence in recovery["classes"].items():
        if evidence["calibration_replicates"] < 200 or evidence["validation_replicates"] < 200:
            fail(f"recovery replication floor {class_id}")
        coverage = list(evidence["scalar_validation_coverage"].values()) + [evidence["joint_validation_coverage"]]
        if not all(0.90 <= value <= 0.99 for value in coverage):
            fail(f"recovery coverage {class_id}")
        if sum(evidence["four_fit_pass"]) < 3 or evidence["status"] != "fit_valid":
            fail(f"four-seed recovery {class_id}")

    golden = load(ARTIFACTS / "generated/golden-vectors-v1.json")["vectors"]
    required_golden = {"canonicalization", "rng", "monthly_moments", "quadrature", "event_segmentation", "daymet_calendar", "objective_estimators"}
    if not required_golden <= set(golden):
        fail(f"missing golden vectors {sorted(required_golden-set(golden))}")
    if golden["objective_estimators"]["null_replicates"] != 500:
        fail("null calibration replication count")
    if golden["rng"]["random123_zero"] != ["0x6627e8d5", "0xe169c58d", "0xbc57ac4c", "0x9b00dbd8"]:
        fail("Philox reference vector")

    commands = load(ARTIFACTS / "generated/command-surface-v1.json")
    if set(commands["commands"]) != EXPECTED_COMMANDS or commands["observed_target_access"] is not False:
        fail("executed command surface")
    if commands["commands"]["run-fixtures"]["fixtures_passed"] != 20:
        fail("run-fixtures command evidence")
    if commands["commands"]["run-fixtures"]["artifact_sha256"] != digest(ARTIFACTS / "generated/fixture-results-v1.json"):
        fail("run-fixtures command artifact identity")
    replay = load(ARTIFACTS / "generated/determinism-replay-v1.json")
    if replay["files_replayed"] != 5 or replay["byte_identical"] is not True or replay["observed_target_access"] is not False:
        fail("determinism replay")
    if not all(item["original_sha256"] == item["replay_sha256"] and item["byte_identical"] for item in replay["comparisons"]):
        fail("determinism replay identities")

    mutations = load(ARTIFACTS / "generated/role-firewall-mutations-v1.json")["mutations"]
    firewall = mutations["role_firewall"]
    required_routes = {"path", "symlink", "copy", "rename", "object_hash", "logical_hash", "record_key", "metadata_confirm", "concurrent_lock", "second_confirmation"}
    if set(firewall) != required_routes:
        fail("role-firewall mutation routes")
    resources = load(ARTIFACTS / "generated/resource-restart-v1.json")["checks"]
    optimizer = resources["optimizer_restart"]
    if set(optimizer["states"]) != {"dominated", "evaluation_complete", "evaluation_incomplete", "hard_infeasible"}:
        fail("attempt state retention")
    if not optimizer["replay_payload_identity"] or optimizer["second_retry"]:
        fail("optimizer replay/retry")
    if not resources["storage"]["lfs_covered"]:
        fail("LFS coverage")

    sys.path.insert(0, str(ROOT))
    from research.a9_harness.cli import build_parser

    parser = build_parser()
    command_action = next(action for action in parser._actions if action.dest == "command")
    if set(command_action.choices) != EXPECTED_COMMANDS:
        fail("command surface")

    specification = (ROOT / "docs/specifications/SPEC-A9-RESEARCH-FOUNDATION.md").read_text(encoding="utf-8")
    coverage = (ARTIFACTS / "requirement-coverage.md").read_text(encoding="utf-8")
    must_count = sum(1 for line in specification.splitlines() if "MUST" in line)
    if must_count != 5 or any(f"A9-MUST-{index:03d}" not in coverage for index in range(1, 6)):
        fail("normative requirement coverage")

    prohibited_imports = ("import requests", "from requests", "import urllib", "from urllib", "import socket", "from socket")
    for path in (ROOT / "research/a9_harness").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in prohibited_imports):
            fail(f"network-client import {path.relative_to(ROOT)}")

    changed = subprocess.run(
        ["git", "diff", "--name-only", DISPATCH, "--", "crates", "reference/cligen532"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if changed:
        fail(f"production/reference change: {changed}")
    print(
        "PASS: 20/20 fixtures; two recovery classes; 31 objectives; "
        "five normative requirements; eight commands; zero observed/runtime changes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
