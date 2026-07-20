#!/usr/bin/env python3
"""Verify the R14R1 operational schema and byte-exact science inheritance."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

package = Path(__file__).resolve().parents[1]
parent = package.parent / "20260720-a10m5r14-continuous-distribution-head-factorial"
repo = package.parents[2]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


inheritance = json.loads(
    (package / "artifacts/inheritance-manifest.json").read_text(encoding="utf-8")
)
profile = inheritance["evidence_profile"]
if digest(repo / profile["path"]) != profile["sha256"]:
    raise RuntimeError("R14 xlarge-evidence profile drift")
parent_plan = json.loads(
    (parent / "artifacts/execution-plan-template.json").read_text(encoding="utf-8")
)
if (
    parent_plan["evidence_profile_path"] != profile["path"]
    or parent_plan["evidence_profile_sha256"] != profile["sha256"]
    or parent_plan["gpu_minute_ceiling"] != 995
    or parent_plan["candidate_concurrency"] != 4
):
    raise RuntimeError("R14 profile/concurrency/resource inheritance drift")
for name, expected in inheritance["science_asset_sha256"].items():
    if name.endswith(".py"):
        path = parent / "artifacts/jobs" / name
    else:
        path = parent / "artifacts" / name
    if digest(path) != expected:
        raise RuntimeError(f"R14 science inheritance drift: {name}")

abort_path = package / "artifacts/parent-pre-submission-abort.json"
abort = json.loads(abort_path.read_text(encoding="utf-8"))
semantic = dict(abort)
recorded = semantic.pop("record_sha256")
canonical = json.dumps(semantic, separators=(",", ":"), sort_keys=True).encode()
if (
    digest(abort_path) != inheritance["parent_abort_sha256"]
    or hashlib.sha256(canonical).hexdigest() != recorded
    or recorded != "65dfe82ad1b149fdb0dbf1b10555d574286b2f6d2e6a31c6cfbb17412acd29ac"
    or abort["terminal"] != "LEMHI-TOOLKIT-RUN-ABORTED-BEFORE-SUBMISSION"
    or abort["remote_absent"] is not True
):
    raise RuntimeError("exact R14 abort pin drift")

capacity = json.loads(
    (package / "artifacts/job-local-capacity-contract.json").read_text(
        encoding="utf-8"
    )
)
roles = [
    "continuous-location-ou-k2",
    "continuous-location-ou-smooth-climatology-k2",
    "continuous-location-scale-ou-k2",
    "continuous-location-scale-ou-smooth-climatology-k2",
]
successor_plan = json.loads(
    (package / "artifacts/execution-plan-template.json").read_text(encoding="utf-8")
)
if (
    successor_plan["submission_waves"]
    != [["control-materialization"], roles]
    or successor_plan["admission_materialization"]["required_roles"]
    != ["control-materialization", *roles]
    or successor_plan["authority_id"]
    != "a10m5r14r1-admission-role-matrix-remedy-r0-authority"
    or successor_plan["resource_budget_id"]
    != "a10m5r14r1-admission-role-matrix-remedy-r0-budget"
    or successor_plan["science_terminals"] != inheritance["science_terminals"]
):
    raise RuntimeError("fresh static execution identity/wave drift")
if capacity["admission"] != {
    "admission_closes_after_any_observed_candidate_failure": True,
    "control_must_pass_before_candidates": True,
    "maximum_live_candidate_jobs": 4,
    "maximum_simultaneous_bootstraps": 1,
    "waves": [roles],
}:
    raise RuntimeError("complete inherited admission schema drift")
if capacity["resources"] != {
    "attempts_per_role": 1,
    "candidate_minutes_each": 240,
    "candidate_role_count": 4,
    "control_minutes": 30,
    "distributed_training": False,
    "gpus_per_role": 1,
    "job_arrays": False,
    "recovery_minutes": 5,
    "scientific_retries": False,
    "total_gpu_minute_ceiling": 995,
}:
    raise RuntimeError("R14 resource freeze drift")
if (
    capacity["calendar_preflight_before_reservation"] is not True
    or capacity["protected_roles_opened"] != []
):
    raise RuntimeError("calendar/protected-role firewall drift")

checker = (package / "artifacts/jobs/admission_checker.py").read_text(
    encoding="utf-8"
)
required = (
    "attempt_key_identity",
    "actual_candidate_roles == expected_candidate_roles",
    'state_name == "SUBMITTED"',
    'state_name == "RESULT_VALIDATED"',
    "expected_setup_roles.add(role)",
    "same_wave_job_receipts",
)
if not all(item in checker for item in required):
    raise RuntimeError("published exact-prefix admission checker drift")
if "a10m5r14-submission-admission" in checker:
    raise RuntimeError("parent admission record type survived")

portfolio = json.loads(
    (parent / "artifacts/portfolio-contract.json").read_text(encoding="utf-8")
)
if set(portfolio["terminals"].values()) != set(inheritance["science_terminals"]):
    raise RuntimeError("R14 science terminal drift")
print("A10M5R14R1-CONTRACT-TEST-PASS")
