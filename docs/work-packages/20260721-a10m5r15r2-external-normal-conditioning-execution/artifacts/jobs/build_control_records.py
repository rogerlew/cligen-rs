#!/usr/bin/env python3
"""Build fresh A10M5R15R2 toolkit authority and two-wave plan."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PARENT_COMMIT = "719d83451ddff698b280219708f7648ff73c8f9d"
PARENT_PACKAGE = "20260720-a10m5r14r2r2-two-l40-two-wave-portfolio"
SOURCE = PACKAGE.parent / PARENT_PACKAGE / "artifacts/jobs/build_control_records.py"
PACKAGE_ID = "20260721-a10m5r15r2-external-normal-conditioning-execution"
RUN_ID = "a10m5r15r2-external-normal-conditioning-execution-r0"
RECORD_TYPE = "a10m5r15r2-submission-admission"
PORTFOLIO_ROLE = "external-normal-conditioning-portfolio"
R1 = PACKAGE.parent / "20260721-a10m5r15r1-prism-eligible-cohort"
CALIBRATION = PACKAGE / "artifacts/attribution-calibration.json"
ROLES = (
    ("e0-centered-location-ou-smooth-climatology-k2", "centered_location_ou_smooth_climatology", "K2"),
    ("e1-normal-conditioned-smooth-climatology-k2", "normal_conditioned_smooth_climatology", "K2"),
    ("e2c-descriptor-anchored-residual-v1", "descriptor_anchored_residual", "K2"),
    ("e2-normal-anchored-residual-v1", "normal_anchored_residual", "K2"),
)
P2_ROLES = {ROLES[0][0], ROLES[1][0]}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_bytes(commit: str, path: Path) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path.relative_to(REPO).as_posix()}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


if SOURCE.read_bytes() != git_bytes(PARENT_COMMIT, SOURCE):
    raise RuntimeError("R14R2R2 builder differs from published parent bytes")
spec = importlib.util.spec_from_file_location("inherited_r15r2_builder", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load inherited authority builder")
parent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parent
spec.loader.exec_module(parent)
inherited = parent.inherited
base_authority = parent.authority
base_plan = parent.plan
base_evidence = inherited.evidence


def predecessor_bundle(record_commit: str | None = None) -> dict:
    package_path = R1 / "package.md"
    disposition_path = R1 / "disposition.md"
    receipt_path = R1 / "artifacts/cohort-build-receipt.json"
    conditioning_path = R1 / "artifacts/normal-conditioning/normal-conditioning-receipt.json"
    if "Status: `A10M5R15R1-COHORT-READY`" not in package_path.read_text(encoding="utf-8"):
        raise RuntimeError("A10M5R15R1 terminal drift")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    conditioning = json.loads(conditioning_path.read_text(encoding="utf-8"))
    if receipt.get("valid") is not True or conditioning.get("valid") is not True or not all(conditioning["gates"].values()):
        raise RuntimeError("A10M5R15R1 evidence invalid")
    files = {
        path.relative_to(REPO).as_posix(): {"bytes": path.stat().st_size, "sha256": digest(path)}
        for path in (package_path, disposition_path, receipt_path, conditioning_path)
    }
    if record_commit is not None:
        for relative in files:
            if git_bytes(record_commit, REPO / relative) != (REPO / relative).read_bytes():
                raise RuntimeError("A10M5R15R1 evidence differs from published source")
    return {
        "files": files,
        "package_id": R1.name,
        "record_commit": record_commit,
        "terminal": "A10M5R15R1-COHORT-READY",
    }


def calibration_bundle(record_commit: str | None = None) -> dict:
    value = json.loads(CALIBRATION.read_text(encoding="utf-8"))
    if not (
        value.get("package_id") == PACKAGE_ID
        and value.get("valid") is True
        and value.get("candidate_output_accessed") is False
        and value.get("protected_roles_opened") == []
        and value.get("sequence_seeds") == [410542, 410543]
        and all(value.get("gates", {}).values())
    ):
        raise RuntimeError("attribution calibration receipt invalid")
    if record_commit is not None and git_bytes(record_commit, CALIBRATION) != CALIBRATION.read_bytes():
        raise RuntimeError("attribution calibration differs from published source")
    return {
        "artifact": {"bytes": CALIBRATION.stat().st_size, "sha256": digest(CALIBRATION)},
        "candidate_output_accessed": False,
        "record_sha256": value["record_sha256"],
        "source_commit": value["source_commit"],
        "valid": True,
    }
def authority(options) -> None:
    predecessor_bundle(options.source_commit)
    calibration_bundle(options.source_commit)
    base_authority(options)
    value = json.loads(options.output.read_text(encoding="utf-8"))
    value.update(
        {
            "package_id": PACKAGE_ID,
            "attribution_calibration": calibration_bundle(options.source_commit),
            "predecessor_package_evidence": predecessor_bundle(options.source_commit),
            "resource_ceiling_gpu_minutes": 515,
            "resource_class": "one-control-plus-one-two-l40-two-wave-external-normal-conditioning",
        }
    )
    parent.parent.rewrite(options.output, value)


def plan(options) -> None:
    predecessor_bundle(options.source_commit)
    calibration_bundle(options.source_commit)
    base_plan(options)
    value = json.loads(options.output.read_text(encoding="utf-8"))
    value["package_id"] = PACKAGE_ID
    value["run_id"] = RUN_ID
    value["predecessor_package_evidence"] = predecessor_bundle(options.source_commit)
    value["attribution_calibration"] = calibration_bundle(options.source_commit)
    value["admission_materialization"]["record_type"] = RECORD_TYPE
    portfolio = next(job for job in value["jobs"] if job["role"] == PORTFOLIO_ROLE)
    portfolio.update({"gpus": 2, "gres": "gpu:l40:2", "time_limit_minutes": 240})
    if [(job["role"], job["gpus"], job["time_limit_minutes"]) for job in value["jobs"]] != [
        ("control-materialization", 1, 30),
        (PORTFOLIO_ROLE, 2, 240),
    ]:
        raise RuntimeError("A10M5R15R2 resource plan drift")
    parent.parent.rewrite(options.output, value)


def evidence(role: str) -> list[str]:
    values = base_evidence(role)
    if role in P2_ROLES:
        values.extend(
            f"results/{role}/seed-work/{seed}/control-export.pt"
            for seed in (147031, 271828, 314159)
        )
    return values


parent.PACKAGE_ID = PACKAGE_ID
parent.RUN_ID = RUN_ID
parent.RECORD_TYPE = RECORD_TYPE
parent.PORTFOLIO_ROLE = PORTFOLIO_ROLE
parent.predecessor_bundle = predecessor_bundle
inherited.PACKAGE_ID = PACKAGE_ID
inherited.PACKAGE = PACKAGE
inherited.ROLES = ROLES
inherited.RUN_ID = RUN_ID
inherited.AUTHORITY_ID = f"{RUN_ID}-authority"
inherited.BUDGET_ID = f"{RUN_ID}-budget"
inherited.AUTHORITY_TOKEN = f"{RUN_ID}-authority-token"
inherited.PREDECESSOR_COMMIT = PARENT_COMMIT
inherited.predecessor_bundle = predecessor_bundle
inherited.operational_predecessor_bundle = predecessor_bundle
inherited.evidence = evidence
inherited.authority = authority
inherited.plan = plan
parent.authority = authority
parent.plan = plan


if __name__ == "__main__":
    inherited.main()
