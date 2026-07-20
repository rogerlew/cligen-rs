#!/usr/bin/env python3
"""Build R14 authority and four-candidate plan with hardened controls."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

parent_path = (
    Path(__file__).resolve().parents[3]
    / "20260719-a10m5r12r1-admission-materialization-remedy"
    / "artifacts/jobs/build_control_records.py"
)
spec = importlib.util.spec_from_file_location("inherited_build_control_records", parent_path)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load inherited authority builder")
inherited = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inherited)

PACKAGE_ID = "20260720-a10m5r14-continuous-distribution-head-factorial"
RUN_ID = "a10m5r14-continuous-distribution-head-factorial-r0"
RECORD_TYPE = "a10m5r14-submission-admission"
CAMPAIGN_COMMIT = "4720ea5764fe02c55a3707f94bb6805f5886b812"
ROLES = (
    ("continuous-location-ou-k2", "centered_location_ou", "K2"),
    ("continuous-location-ou-smooth-climatology-k2", "centered_location_ou_smooth_climatology", "K2"),
    ("continuous-location-scale-ou-k2", "centered_location_and_scale_ou", "K2"),
    ("continuous-location-scale-ou-smooth-climatology-k2", "centered_location_and_scale_ou_smooth_climatology", "K2"),
)
CAMPAIGN_FILES = (
    "docs/work-packages/20260720-a10m5r13r2-semantic-plan-replay-authentication-remedy/artifacts/execution/temporal-result.json",
    "docs/work-packages/20260720-a10m5r13r2-semantic-plan-replay-authentication-remedy/artifacts/execution/replay-identity.json",
    "docs/work-packages/20260720-a10m5r13r2-semantic-plan-replay-authentication-remedy/closeout-review.md",
    "docs/work-packages/20260720-a10m5r13r2-semantic-plan-replay-authentication-remedy/package.md",
)
SCIENCE_FILES = (
    "docs/work-packages/20260720-a10m5r14-continuous-distribution-head-factorial/artifacts/science-contract.json",
    "docs/work-packages/20260720-a10m5r14-continuous-distribution-head-factorial/artifacts/portfolio-contract.json",
    "docs/work-packages/20260720-a10m5r14-continuous-distribution-head-factorial/artifacts/temporal-contract.json",
    "docs/work-packages/20260720-a10m5r14-continuous-distribution-head-factorial/artifacts/objective-selector-coverage.json",
    "docs/work-packages/20260720-a10m5r14-continuous-distribution-head-factorial/artifacts/jobs/continuous_core.py",
    "docs/work-packages/20260720-a10m5r14-continuous-distribution-head-factorial/artifacts/jobs/aligned_objective.py",
)


def bundle(commit: str, package_id: str, files: tuple[str, ...]) -> dict:
    inherited.verify_commit(commit)
    rows = {}
    for relative in files:
        payload = inherited.git_bytes(commit, relative)
        path = inherited.REPO / relative
        if path.read_bytes() != payload:
            raise RuntimeError(f"predecessor source drift: {relative}")
        rows[relative] = {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    return {"files": rows, "package_id": package_id, "record_commit": commit}


def current_published_commit() -> str:
    head = inherited.subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=inherited.REPO, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    upstream = inherited.subprocess.run(
        ("git", "rev-parse", "origin/main"), cwd=inherited.REPO, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    branch = inherited.subprocess.run(
        ("git", "branch", "--show-current"), cwd=inherited.REPO, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    if head != upstream or branch != "main":
        raise RuntimeError("R14 predecessor requires exact published main")
    return head


def campaign_bundle() -> dict:
    value = bundle(
        CAMPAIGN_COMMIT,
        "20260720-a10m5r13r2-semantic-plan-replay-authentication-remedy",
        CAMPAIGN_FILES,
    )
    result = json.loads((inherited.REPO / CAMPAIGN_FILES[0]).read_text(encoding="utf-8"))
    if result.get("terminal") != "HOLD-A10M5R13-NO-TEMPORALLY-ELIGIBLE-CANDIDATE" or result.get("eligible_configurations") != [] or result.get("protected_roles_opened") != []:
        raise RuntimeError("campaign predecessor hold/firewall drift")
    return value


def science_bundle(source_commit: str) -> dict:
    return bundle(
        source_commit,
        PACKAGE_ID,
        SCIENCE_FILES,
    )


def rewrite_record(path: Path, changes: dict) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    value.update(changes)
    inherited.write(path, value)


base_authority = inherited.authority
base_plan = inherited.plan


def authority(options) -> None:
    base_authority(options)
    coverage_path = options.asset_root / "objective-selector-coverage.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    if coverage.get("counts", {}).get("total") != 188 or len(coverage.get("metrics", [])) != 188:
        raise RuntimeError("prospective objective-selector coverage gate failed")
    rewrite_record(options.output, {
        "resource_ceiling_gpu_minutes": 995,
        "resource_class": "four-concurrent-l40-continuous-distribution-head-factorial",
        "prospective_objective_selector_coverage": {
            "bytes": coverage_path.stat().st_size,
            "metric_count": 188,
            "sha256": inherited.digest(coverage_path),
            "valid": True,
        },
    })


def plan(options) -> None:
    base_plan(options)
    value = json.loads(options.output.read_text(encoding="utf-8"))
    for job in value["jobs"]:
        if job["role"] != "control-materialization":
            job["time_limit_minutes"] = 240
    value["admission_materialization"]["record_type"] = RECORD_TYPE
    value["submission_waves"] = [
        ["control-materialization"],
        [role for role, _, _ in ROLES],
    ]
    value["evidence_profile"] = {
        "path": "research/a10/lemhi_toolkit/profiles/lemhi-v2-xlarge-evidence.json",
        "sha256": "ebf36a6cda19491a00bf6f56ec64cec30ca28f60eaa2b07fa5bd92dd8c668629",
        "estimated_expanded_bytes": 192000000,
        "maximum_expanded_bytes": 256000000,
        "maximum_file_bytes": 64000000,
    }
    value["evidence_volume"] = {
        "maximum_expanded_bytes": 256000000,
        "maximum_file_bytes": 64000000,
        "maximum_files": len(value["evidence_allowlist"]),
    }
    inherited.write(options.output, value)


inherited.PACKAGE_ID = PACKAGE_ID
inherited.RUN_ID = RUN_ID
inherited.AUTHORITY_ID = f"{RUN_ID}-authority"
inherited.BUDGET_ID = f"{RUN_ID}-budget"
inherited.AUTHORITY_TOKEN = f"{RUN_ID}-authority-token"
inherited.ROLES = ROLES
inherited.PREDECESSOR_COMMIT = CAMPAIGN_COMMIT
inherited.predecessor_bundle = campaign_bundle
inherited.operational_predecessor_bundle = science_bundle
inherited.authority = authority
inherited.plan = plan


if __name__ == "__main__":
    inherited.main()
