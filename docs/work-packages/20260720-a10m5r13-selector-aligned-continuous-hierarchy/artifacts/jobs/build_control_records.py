#!/usr/bin/env python3
"""Build R13 authority and plan using the hardened R12R1 implementation."""

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

PACKAGE_ID = "20260720-a10m5r13-selector-aligned-continuous-hierarchy"
RUN_ID = "a10m5r13-selector-aligned-continuous-hierarchy-r0"
RECORD_TYPE = "a10m5r13-submission-admission"
CAMPAIGN_COMMIT = "4ebc8c6124e5d024dc74327789cd01a3cf5f0d2e"
SCIENCE_COMMIT = "87d38996e1f46ddb47b80c16c9625c16beaede9b"
ROLES = (
    ("selector-aligned-continuous-hierarchy-k2", "selector_aligned_continuous_hierarchy", "K2"),
    ("selector-aligned-shared-slow-climate-state-k2", "selector_aligned_shared_slow_climate_state", "K2"),
)
CAMPAIGN_FILES = (
    "docs/work-packages/20260720-a10m5r12r2-collection-ceiling-reconciliation/artifacts/evidence-identity.json",
    "docs/work-packages/20260720-a10m5r12r2-collection-ceiling-reconciliation/artifacts/execution-disposition.md",
    "docs/work-packages/20260720-a10m5r12r2-collection-ceiling-reconciliation/artifacts/execution-gates.md",
    "docs/work-packages/20260720-a10m5r12r2-collection-ceiling-reconciliation/artifacts/execution-review.md",
    "docs/work-packages/20260720-a10m5r12r2-collection-ceiling-reconciliation/package.md",
)
SCIENCE_FILES = (
    "docs/work-packages/20260719-a10m5r12r1-admission-materialization-remedy/artifacts/portfolio-contract.json",
    "docs/work-packages/20260719-a10m5r12r1-admission-materialization-remedy/artifacts/temporal-contract.json",
    "docs/work-packages/20260719-a10m5r12r1-admission-materialization-remedy/artifacts/jobs/continuous_core.py",
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


def campaign_bundle() -> dict:
    value = bundle(
        CAMPAIGN_COMMIT,
        "20260720-a10m5r12r2-collection-ceiling-reconciliation",
        CAMPAIGN_FILES,
    )
    identity = json.loads((inherited.REPO / CAMPAIGN_FILES[0]).read_text(encoding="utf-8"))
    if identity.get("terminal") != "HOLD-A10M5R12-NO-TEMPORALLY-ELIGIBLE-CANDIDATE" or identity.get("protected_roles_opened") != []:
        raise RuntimeError("campaign predecessor hold/firewall drift")
    return value


def science_bundle(_source_commit: str) -> dict:
    return bundle(
        SCIENCE_COMMIT,
        "20260719-a10m5r12r1-admission-materialization-remedy",
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
    rewrite_record(options.output, {
        "resource_ceiling_gpu_minutes": 515,
        "resource_class": "two-concurrent-l40-selector-aligned-continuous-hierarchy",
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
        [ROLES[0][0], ROLES[1][0]],
    ]
    value["evidence_profile"] = {
        "path": "research/a10/lemhi_toolkit/profiles/lemhi-v2-large-evidence.json",
        "sha256": "fba24ee726285f2a0cba55d69ed9c4949145ac072514bc8e31ee4941d55d0b45",
        "estimated_expanded_bytes": 96000000,
        "maximum_expanded_bytes": 128000000,
        "maximum_file_bytes": 64000000,
    }
    value["evidence_volume"] = {
        "maximum_expanded_bytes": 128000000,
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
