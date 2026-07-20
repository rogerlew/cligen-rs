#!/usr/bin/env python3
"""Build R14R2 authority and a two-role shared-environment portfolio plan."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PARENT_COMMIT = "bbb3075109ce06dabda13d43862cd94d375225bd"
PARENT_BUILDER = (
    PACKAGE.parent
    / "20260720-a10m5r14-continuous-distribution-head-factorial"
    / "artifacts/jobs/build_control_records.py"
)
PACKAGE_ID = "20260720-a10m5r14r2-shared-environment-four-l40-portfolio"
RUN_ID = "a10m5r14r2-shared-environment-four-l40-portfolio-r0"
RECORD_TYPE = "a10m5r14r2-submission-admission"
PORTFOLIO_ROLE = "continuous-distribution-head-factorial-portfolio"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def failure_bundle(record_commit: str | None = None) -> dict:
    prepare_path = PACKAGE / "artifacts/jobs/prepare_assets.py"
    prepare_spec = importlib.util.spec_from_file_location("r14r2_prepare_assets", prepare_path)
    if prepare_spec is None or prepare_spec.loader is None:
        raise RuntimeError("cannot load R14R2 predecessor verifier")
    prepare = importlib.util.module_from_spec(prepare_spec)
    prepare_spec.loader.exec_module(prepare)
    verified = prepare.verify_predecessor(PACKAGE)
    contract = json.loads((PACKAGE / "artifacts/predecessor-evidence-contract.json").read_text())
    binding = contract["execution_bindings"]
    path = REPO / binding["path"]
    result = {
        "actual_gpu_minutes": verified["actual_gpu_minutes"],
        "artifact": {"bytes": path.stat().st_size, "sha256": binding["sha256"]},
        "artifact_source_path": path.relative_to(REPO).as_posix(),
        "failures": verified["failures"],
        "ledger_head_sha256": verified["ledger"]["head_sha256"],
        "matrix_stop_record_sha256": verified["matrix_stop"]["record_sha256"],
        "package_id": "20260720-a10m5r14r1-admission-role-matrix-remedy",
        "plan_id": verified["plan_id"],
        "source_commit": verified["source_commit"],
        "terminal": verified["terminal"],
    }
    if record_commit is not None:
        inherited.verify_commit(record_commit)
        relative = path.relative_to(REPO).as_posix()
        if inherited.git_bytes(record_commit, relative) != path.read_bytes():
            raise RuntimeError("R14R1 failure artifact differs from published R14R2 bytes")
        result["artifact_record_commit"] = record_commit
    return result


spec = importlib.util.spec_from_file_location("r14_build_control_records", PARENT_BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load authenticated R14 authority builder")
parent = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parent)
inherited = parent.inherited
base_authority = parent.authority
base_plan = parent.plan


def science_bundle(source_commit: str) -> dict:
    return parent.science_bundle(source_commit)


def rewrite(path: Path, value: dict) -> None:
    inherited.write(path, value)


def authority(options) -> None:
    failure_bundle(options.source_commit)
    predecessor = failure_bundle()
    base_authority(options)
    value = json.loads(options.output.read_text())
    value.update(
        {
            "predecessor_package_evidence": predecessor,
            "resource_ceiling_gpu_minutes": 995,
            "resource_class": "one-four-l40-shared-environment-continuous-distribution-head-factorial",
        }
    )
    rewrite(options.output, value)


def science_evidence(role: str) -> list[str]:
    root = f"results/{role}"
    return [
        f"admissions/{role}.json",
        f"{root}/calendar-preflight.json",
        f"{root}/candidate-summary.json",
        f"{root}/control-identity.json",
        f"{root}/streams.json",
        f"{root}/streams.npz",
        *(f"{root}/seeds/{seed}.json" for seed in inherited.SEEDS),
        *(f"{root}/seed-work/{seed}/checkpoint.pt" for seed in inherited.SEEDS),
        f"{root}/training.json",
        f"{root}/candidate.stderr",
        f"{root}/process.json",
        f"{root}/evidence.json",
    ]


def plan(options) -> None:
    failure_bundle(options.source_commit)
    predecessor = failure_bundle()
    base_plan(options)
    value = json.loads(options.output.read_text())
    control = next(job for job in value["jobs"] if job["role"] == "control-materialization")
    portfolio = {
        "cpus": 32,
        "expected_exit_code": 0,
        "gate_receipt": f"results/{PORTFOLIO_ROLE}/evidence.json",
        "gpus": 4,
        "gres": "gpu:l40:4",
        "max_attempts": 1,
        "memory_mb": 131072,
        "partition": "gpu-icrews",
        "retry_on": [],
        "role": PORTFOLIO_ROLE,
        "script": f"job-{PORTFOLIO_ROLE}.sh",
        "time_limit_minutes": 240,
    }
    value["jobs"] = [control, portfolio]
    value["submission_waves"] = [["control-materialization"], [PORTFOLIO_ROLE]]
    value["admission_materialization"].update(
        {"record_type": RECORD_TYPE, "required_roles": ["control-materialization", PORTFOLIO_ROLE]}
    )
    value["immediate_pre_submit_occupancy"] = {
        "active_states": ["RUNNING", "COMPLETING", "CONFIGURING"],
        "maximum_capture_seconds": 15,
        "node": "node03",
        "required_idle_l40_count": 4,
        "required_role": PORTFOLIO_ROLE,
        "receipt": f"admissions/{PORTFOLIO_ROLE}-occupancy.json",
    }
    allowlist = ["recovery.json", "slurm/toolkit-recovery.0.err", "slurm/toolkit-recovery.0.out"]
    allowlist.extend(inherited.evidence("control-materialization"))
    allowlist.extend(
        [
            f"admissions/{PORTFOLIO_ROLE}.json",
            f"admissions/{PORTFOLIO_ROLE}-occupancy.json",
            f"results/{PORTFOLIO_ROLE}/evidence.json",
            f"results/{PORTFOLIO_ROLE}/cleanup-permissions.json",
            f"results/{PORTFOLIO_ROLE}/launcher.json",
            f"results/{PORTFOLIO_ROLE}/setup.json",
            f"results/{PORTFOLIO_ROLE}/setup.log",
            f"results/{PORTFOLIO_ROLE}/storage-preflight.json",
            f"results/{PORTFOLIO_ROLE}/supervisor.json",
            f"slurm/{PORTFOLIO_ROLE}.0.err",
            f"slurm/{PORTFOLIO_ROLE}.0.out",
        ]
    )
    for role, _, _ in parent.ROLES:
        allowlist.extend(science_evidence(role))
    value["evidence_allowlist"] = allowlist
    value["evidence_volume"]["maximum_files"] = len(allowlist)
    value["job_local_capacity"] = {
        "checkpoint_bytes": 2147483648,
        "expanded_asset_bytes": 11811160064,
        "margin_bytes": 2147483648,
        "minimum_free_bytes": 17179869184,
        "product_bytes": 1073741824,
        "required_inodes": 16000,
        "shared_environment_count": 1,
        "shared_corpus_count": 1,
    }
    value["predecessor_package_evidence"] = predecessor
    value["providers"] = [
        "research/a10/lemhi_toolkit/providers/accelerator-l40-multigpu-v1.json"
        if item.endswith("accelerator-l40-v2.json")
        else item
        for item in value["providers"]
    ]
    rewrite(options.output, value)


inherited.PACKAGE_ID = PACKAGE_ID
inherited.RUN_ID = RUN_ID
inherited.AUTHORITY_ID = f"{RUN_ID}-authority"
inherited.BUDGET_ID = f"{RUN_ID}-budget"
inherited.AUTHORITY_TOKEN = f"{RUN_ID}-authority-token"
inherited.ROLES = parent.ROLES
inherited.PREDECESSOR_COMMIT = PARENT_COMMIT
inherited.predecessor_bundle = failure_bundle
inherited.operational_predecessor_bundle = science_bundle
inherited.authority = authority
inherited.plan = plan

if __name__ == "__main__":
    inherited.main()
