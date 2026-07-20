#!/usr/bin/env python3
"""Verify the frozen R14R2 operational and science contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


execution = json.loads((PACKAGE / "artifacts/execution-plan-template.json").read_text())
capacity = json.loads((PACKAGE / "artifacts/job-local-capacity-contract.json").read_text())
role_map = json.loads((PACKAGE / "artifacts/portfolio-role-map.json").read_text())
binding = json.loads((PACKAGE / "artifacts/device-binding-qualification.json").read_text())
inheritance = json.loads((PACKAGE / "artifacts/inheritance-manifest.json").read_text())

portfolio = "continuous-distribution-head-factorial-portfolio"
roles = [row["role"] for row in role_map["processes"]]
expected_roles = [
    "continuous-location-ou-k2",
    "continuous-location-ou-smooth-climatology-k2",
    "continuous-location-scale-ou-k2",
    "continuous-location-scale-ou-smooth-climatology-k2",
]
assert execution["submission_waves"] == [["control-materialization"], [portfolio]]
assert execution["gpu_minute_ceiling"] == 30 + 4 * 240 + 5 == 995
assert execution["portfolio_gpus"] == 4
assert capacity["resources"]["allocation_job_count"] == 1
assert capacity["resources"]["candidate_role_count"] == 1
assert capacity["resources"]["science_arm_count"] == 4
assert capacity["resources"]["independent_process_count"] == 4
assert capacity["shared_environment"]["bootstrap_count"] == 1
assert capacity["shared_environment"]["corpus_extraction_count"] == 1
assert capacity["shared_environment"]["uses_ddp"] is False
assert capacity["shared_environment"]["uses_nccl"] is False
assert capacity["shared_environment"]["uses_torchrun"] is False
assert roles == expected_roles
assert [row["slot"] for row in role_map["processes"]] == list(range(4))
assert [row["allocation_token_index"] for row in role_map["processes"]] == list(range(4))
assert all(row["capacity"] == "K2" for row in role_map["processes"])
assert "cuda_visible_devices" not in json.dumps(role_map)
binding_evidence = REPO / binding["evidence"]["path"]
assert {"bytes": binding_evidence.stat().st_size, "sha256": digest(binding_evidence)} == {
    "bytes": binding["evidence"]["bytes"],
    "sha256": binding["evidence"]["sha256"],
}
assert binding["binding_contract"]["uuid_dependency"] is False
assert all(binding["gates"].values())
assert inheritance["protected_roles_opened"] == []
assert inheritance["science_terminals"] == [
    "A10M5R14-TEMPORAL-READY",
    "HOLD-A10M5R14-NO-TEMPORALLY-ELIGIBLE-CANDIDATE",
]

science_paths = {
    "aligned_objective.py": PACKAGE.parent
    / "20260720-a10m5r14-continuous-distribution-head-factorial/artifacts/jobs/aligned_objective.py",
    "climate_core.py": PACKAGE.parent
    / "20260720-a10m5r14-continuous-distribution-head-factorial/artifacts/jobs/climate_core.py",
    "continuous_core.py": PACKAGE.parent
    / "20260720-a10m5r14-continuous-distribution-head-factorial/artifacts/jobs/continuous_core.py",
    "objective-selector-coverage.json": PACKAGE.parent
    / "20260720-a10m5r14-continuous-distribution-head-factorial/artifacts/objective-selector-coverage.json",
    "portfolio-contract.json": PACKAGE.parent
    / "20260720-a10m5r14-continuous-distribution-head-factorial/artifacts/portfolio-contract.json",
    "science-contract.json": PACKAGE.parent
    / "20260720-a10m5r14-continuous-distribution-head-factorial/artifacts/science-contract.json",
    "temporal-contract.json": PACKAGE.parent
    / "20260720-a10m5r14-continuous-distribution-head-factorial/artifacts/temporal-contract.json",
}
assert {name: digest(path) for name, path in science_paths.items()} == inheritance["science_asset_sha256"]

provider = REPO / "research/a10/lemhi_toolkit/providers/accelerator-l40-multigpu-v1.json"
value = json.loads(provider.read_text())
assert value["name"] == "accelerator-l40-multigpu-v1"
assert value["capability_contract"]["allowed_counts"] == [1, 2, 4]
assert value["capability_contract"]["node"] == "node03"

print("A10M5R14R2-CONTRACTS-PASS")
