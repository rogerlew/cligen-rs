#!/usr/bin/env python3
"""Verify the committed A10M5R10 operational HOLD."""

from __future__ import annotations

import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent.parent


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    artifacts = PACKAGE / "artifacts"
    result = json.loads((artifacts / "operational-summary.json").read_text())
    calendar = json.loads((artifacts / "calendar-preflight.json").read_text())
    terminal = json.loads(
        (artifacts / "toolkit-recovered/terminal.json").read_text()
    )
    cleanup = json.loads(
        (artifacts / "toolkit-recovered/cleanup.json").read_text()
    )

    require(result["terminal"] == "HOLD-A10M5R10-JOB-LOCAL-CAPACITY", "terminal drift")
    require(calendar["valid"] is True, "calendar preflight drift")
    require(result["science"]["control_matrix_passed"] is True, "control drift")
    require(result["science"]["selector_run"] is False, "selector must remain closed")
    require(result["science"]["scientific_interpretation_authorized"] is False, "science overclaim")
    require(not (artifacts / "portfolio-summary.json").exists(), "partial matrix summary published")
    require(not (artifacts / "portfolio-decision.json").exists(), "partial matrix decision published")

    jobs = result["jobs"]
    require(len(jobs) == 11, "attempt count drift")
    require(sum(item["actual_gpu_minutes"] for item in jobs) == 103, "accounting drift")
    failures = [item for item in jobs if not item["passed"]]
    passes = [item for item in jobs if item["passed"]]
    require(len(failures) == 8, "failed role count drift")
    require(
        {item["role"] for item in passes}
        == {
            "control-materialization",
            "physics-conditioned-hierarchical-adapter-k1",
            "physics-conditioned-hierarchical-adapter-k2",
        },
        "passing role set drift",
    )
    require(all(len(item["receipt_sha256"]) == 64 for item in jobs), "receipt identity drift")
    root_cause = result["root_cause"]
    require(root_cause["classification"] == "aggregate-node-local-bootstrap-capacity", "root cause drift")
    require(root_cause["concurrent_bootstraps_in_failed_batches"] == 4, "concurrency drift")
    require(
        root_cause["per_bootstrap_bytes_lower_bound"]
        == root_cause["wheelhouse_archive_bytes"]
        + root_cause["environment_tree_bytes_lower_bound"],
        "bootstrap byte arithmetic drift",
    )
    require(result["execution"]["actual_gpu_minutes"] <= result["authority"]["ceiling_gpu_minutes"], "resource ceiling")
    require(result["execution"]["recovery_invoked"] is False, "unexpected recovery")
    require(terminal["terminal"] == "LEMHI-TOOLKIT-RUN-CLOSED", "toolkit not closed")
    require(terminal["attempt_count"] == 11, "terminal attempt count drift")
    require(terminal["record_sha256"] == result["execution"]["terminal_receipt_sha256"], "terminal receipt drift")
    require(cleanup["remote_absent"] is True, "remote root remains")
    require(cleanup["job_local_cleanup"] == "verified_absent", "job-local cleanup drift")
    require(cleanup["record_sha256"] == result["execution"]["cleanup_receipt_sha256"], "cleanup receipt drift")
    print("A10M5R10-OPERATIONAL-HOLD-VERIFIED")


if __name__ == "__main__":
    main()
