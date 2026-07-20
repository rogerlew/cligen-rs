#!/usr/bin/env python3
"""Build fresh R14R2R1 authority and the unchanged R14R2 plan."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PARENT_COMMIT = "3a9f2aedab1f7be5202a141c7d32350d7fe6f5e3"
SOURCE = PACKAGE.parent / "20260720-a10m5r14r2-shared-environment-four-l40-portfolio/artifacts/jobs/build_control_records.py"
PACKAGE_ID = "20260720-a10m5r14r2r1-inherited-admission-checker-identity-remedy"
RUN_ID = "a10m5r14r2r1-inherited-admission-checker-identity-remedy-r0"
RECORD_TYPE = "a10m5r14r2r1-submission-admission"
CHECKER_ASSETS = {
    "logical_names": ["admission_checker.py", "inherited_admission_checker.py"],
    "protocol": "ordered-plan-assets-v1",
}


def git_bytes(relative: str) -> bytes:
    return subprocess.run(("git", "show", f"{PARENT_COMMIT}:{relative}"), cwd=REPO, check=True, capture_output=True).stdout


def verify_parent() -> None:
    relative = SOURCE.relative_to(REPO).as_posix()
    if SOURCE.read_bytes() != git_bytes(relative):
        raise RuntimeError("R14R2 plan builder differs from published parent bytes")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def predecessor_bundle(record_commit: str | None = None) -> dict:
    path = PACKAGE / "artifacts/parent-pre-submission-abort.json"
    if digest(path) != "7f3c7c6a9e73cb3114310cf7ecf1bcaf5ba82bc9f8cef61710f7598693d33e24":
        raise RuntimeError("R14R2 abort evidence identity drift")
    abort = json.loads(path.read_text())
    value = {
        "actual_gpu_minutes": 0,
        "artifact": {"bytes": path.stat().st_size, "sha256": digest(path)},
        "artifact_source_path": path.relative_to(REPO).as_posix(),
        "package_id": abort["package_id"],
        "plan_id": abort["plan_id"],
        "source_commit": abort["source_commit"],
        "terminal": {
            "job_local_cleanup": abort["job_local_cleanup"],
            "remote_absent": abort["remote_absent"],
            "terminal": abort["terminal"],
        },
    }
    if record_commit is not None:
        published = subprocess.run(("git", "show", f"{record_commit}:{path.relative_to(REPO).as_posix()}"), cwd=REPO, check=True, capture_output=True).stdout
        if published != path.read_bytes():
            raise RuntimeError("R14R2 abort differs from published successor bytes")
        value["artifact_record_commit"] = record_commit
    return value


verify_parent()
spec = importlib.util.spec_from_file_location("r14r2_build_control_records", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load authenticated R14R2 plan builder")
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
inherited = parent.inherited
base_authority = parent.authority
base_plan = parent.plan


def authority(options) -> None:
    predecessor_bundle(options.source_commit)
    base_authority(options)
    value = json.loads(options.output.read_text())
    value["package_id"] = PACKAGE_ID
    value["predecessor_package_evidence"] = predecessor_bundle()
    value["resource_ceiling_gpu_minutes"] = 995
    parent.rewrite(options.output, value)


def plan(options) -> None:
    predecessor_bundle(options.source_commit)
    base_plan(options)
    value = json.loads(options.output.read_text())
    value["package_id"] = PACKAGE_ID
    value["run_id"] = RUN_ID
    value["predecessor_package_evidence"] = predecessor_bundle()
    materialization = value["admission_materialization"]
    materialization["record_type"] = RECORD_TYPE
    materialization["checker_assets"] = CHECKER_ASSETS
    # The inherited R14R2 builder freezes the science, resources, jobs,
    # submission waves, providers, evidence volume, and allowlist unchanged.
    if value.get("resource_ceiling_gpu_minutes", 995) != 995:
        raise RuntimeError("R14R2 resource ceiling drift")
    parent.rewrite(options.output, value)


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
parent.PACKAGE_ID = PACKAGE_ID
parent.RUN_ID = RUN_ID
parent.RECORD_TYPE = RECORD_TYPE
parent.failure_bundle = predecessor_bundle


if __name__ == "__main__":
    inherited.main()
