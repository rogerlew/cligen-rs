#!/usr/bin/env python3
"""Build fresh R14R2R2 authority and the two-L40 two-wave plan."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PARENT_COMMIT = "6463ab2bebcf016c371afc56e31ffc7156a2fb95"
PARENT_PACKAGE = "20260720-a10m5r14r2r1-inherited-admission-checker-identity-remedy"
SOURCE = PACKAGE.parent / PARENT_PACKAGE / "artifacts/jobs/build_control_records.py"
HOLD = PACKAGE.parent / PARENT_PACKAGE / "artifacts/execution-hold.json"
HOLD_SHA256 = "b62a7e1ec7908653f8dd038ca34e9bd43520165fbc7b383d7fc18b7a730e174d"
PACKAGE_ID = "20260720-a10m5r14r2r2-two-l40-two-wave-portfolio"
RUN_ID = "a10m5r14r2r2-two-l40-two-wave-portfolio-r0"
RECORD_TYPE = "a10m5r14r2r2-submission-admission"
PORTFOLIO_ROLE = "continuous-distribution-head-factorial-portfolio"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_bytes(commit: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{relative}"), cwd=REPO, check=True, capture_output=True
    ).stdout


def verify_parent() -> None:
    if SOURCE.read_bytes() != git_bytes(PARENT_COMMIT, SOURCE.relative_to(REPO).as_posix()):
        raise RuntimeError("R14R2R1 builder differs from published parent bytes")


def predecessor_bundle(record_commit: str | None = None) -> dict:
    if digest(HOLD) != HOLD_SHA256:
        raise RuntimeError("R14R2R1 execution hold identity drift")
    value = json.loads(HOLD.read_text())
    if not (
        value.get("source_commit") == PARENT_COMMIT
        and value.get("portfolio_submitted") is False
        and value.get("actual_gpu_minutes") == 19
        and value.get("control", {}).get("passed") is True
        and value.get("terminal") == "R14R2R1-HOLD-FOUR-IDLE-L40-UNAVAILABLE"
    ):
        raise RuntimeError("R14R2R1 execution hold semantic drift")
    bundle = {
        "actual_gpu_minutes": 19,
        "artifact": {"bytes": HOLD.stat().st_size, "sha256": digest(HOLD)},
        "artifact_source_path": HOLD.relative_to(REPO).as_posix(),
        "control_job_id": value["control"]["job_id"],
        "package_id": value["package_id"],
        "plan_id": value["current_plan_id"],
        "portfolio_submitted": False,
        "source_commit": value["source_commit"],
        "terminal": value["terminal"],
    }
    if record_commit is not None:
        if git_bytes(record_commit, HOLD.relative_to(REPO).as_posix()) != HOLD.read_bytes():
            raise RuntimeError("R14R2R1 hold differs from published successor bytes")
        bundle["artifact_record_commit"] = record_commit
    return bundle


verify_parent()
spec = importlib.util.spec_from_file_location("r14r2r1_build_control_records", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load authenticated R14R2R1 builder")
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
inherited = parent.inherited
base_authority = parent.authority
base_plan = parent.plan


def authority(options) -> None:
    predecessor_bundle(options.source_commit)
    base_authority(options)
    value = json.loads(options.output.read_text())
    value.update(
        {
            "package_id": PACKAGE_ID,
            "predecessor_package_evidence": predecessor_bundle(),
            "resource_ceiling_gpu_minutes": 515,
            "resource_class": "one-two-l40-two-wave-continuous-distribution-head-factorial",
        }
    )
    parent.parent.rewrite(options.output, value)


def plan(options) -> None:
    predecessor_bundle(options.source_commit)
    base_plan(options)
    value = json.loads(options.output.read_text())
    value["package_id"] = PACKAGE_ID
    value["run_id"] = RUN_ID
    value["predecessor_package_evidence"] = predecessor_bundle()
    value["admission_materialization"]["record_type"] = RECORD_TYPE
    portfolio = next(job for job in value["jobs"] if job["role"] == PORTFOLIO_ROLE)
    portfolio.update({"gpus": 2, "gres": "gpu:l40:2", "time_limit_minutes": 240})
    value["immediate_pre_submit_occupancy"].update(
        {"required_idle_l40_count": 2, "maximum_capture_seconds": 15}
    )
    if [(job["role"], job["gpus"], job["time_limit_minutes"]) for job in value["jobs"]] != [
        ("control-materialization", 1, 30),
        (PORTFOLIO_ROLE, 2, 240),
    ]:
        raise RuntimeError("R14R2R2 resource plan drift")
    parent.parent.rewrite(options.output, value)


parent.PACKAGE_ID = PACKAGE_ID
parent.RUN_ID = RUN_ID
parent.RECORD_TYPE = RECORD_TYPE
parent.predecessor_bundle = predecessor_bundle
inherited.PACKAGE_ID = PACKAGE_ID
inherited.RUN_ID = RUN_ID
inherited.AUTHORITY_ID = f"{RUN_ID}-authority"
inherited.BUDGET_ID = f"{RUN_ID}-budget"
inherited.AUTHORITY_TOKEN = f"{RUN_ID}-authority-token"
inherited.PREDECESSOR_COMMIT = PARENT_COMMIT
inherited.predecessor_bundle = predecessor_bundle
inherited.operational_predecessor_bundle = predecessor_bundle
inherited.authority = authority
inherited.plan = plan
parent.authority = authority
parent.plan = plan


if __name__ == "__main__":
    inherited.main()
