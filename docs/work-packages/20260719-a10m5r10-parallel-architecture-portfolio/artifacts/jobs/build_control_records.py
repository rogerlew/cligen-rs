#!/usr/bin/env python3
"""Build private A10M5R10 authority input and portfolio plan records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REMOTE_BASE = "/ceph/home/rogerlew.ui/.cligen-rs-a10"
PACKAGE_ID = "20260719-a10m5r10-parallel-architecture-portfolio"
RUN_ID = "a10m5r10-parallel-architecture-portfolio-r0"
AUTHORITY_ID = "a10m5r10-parallel-architecture-portfolio-authority"
BUDGET_ID = "a10m5r10-parallel-architecture-portfolio-budget"
AUTHORITY_TOKEN = "a10m5r10-parallel-architecture-portfolio-authority-token"

CANDIDATES = (
    ("monthly-residual-adapter", "monthly_residual_adapter"),
    ("annual-monthly-residual-adapter", "annual_monthly_residual_adapter"),
    ("hierarchical-joint-factor-adapter", "hierarchical_joint_factor_adapter"),
    (
        "climate-normal-hierarchical-state-space",
        "climate_normal_hierarchical_state_space",
    ),
    (
        "physics-conditioned-hierarchical-adapter",
        "physics_conditioned_hierarchical_adapter",
    ),
)
CAPACITIES = ("K1", "K2")
SEEDS = (147031, 271828, 314159)


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)


def authority(options: argparse.Namespace) -> None:
    contract = json.loads(
        (options.asset_root / "portfolio-contract.json").read_text(encoding="utf-8")
    )
    ceiling = contract["execution"]["total_gpu_minute_ceiling"]
    if ceiling != 935:
        raise RuntimeError("portfolio contract resource ceiling drift")
    value = {
        "allowed_roots": [str(options.asset_root.resolve())],
        "authority_id": AUTHORITY_ID,
        "confirmation_classification": "development-only",
        "genesis_authorized": True,
        "ledger_anchor": str(
            options.state_root.resolve() / "authorities" / BUDGET_ID / "ledger.json"
        ),
        "package_id": PACKAGE_ID,
        "predecessor_evidence": [],
        "published_source_commits": [options.source_commit],
        "push_target": "main",
        "resource_budget_id": BUDGET_ID,
        "resource_ceiling_gpu_minutes": ceiling,
        "resource_class": "one-l40-parallel-architecture-portfolio",
        "scheduler_authority_token": AUTHORITY_TOKEN,
        "scheduler_evidence": [],
        "source_commit": options.source_commit,
        "starting_branch": "main",
    }
    write(options.output, value)


def evidence_for_role(role: str) -> list[str]:
    root = f"results/{role}"
    common = [
        f"{root}/evidence.json",
        f"{root}/supervisor.json",
        f"slurm/{role}.0.err",
        f"slurm/{role}.0.out",
    ]
    if role == "control-materialization":
        return [
            f"{root}/calendar-preflight.json",
            f"{root}/control-identity.json",
            f"{root}/control-summary.json",
            *common,
        ]
    return [
        f"{root}/calendar-preflight.json",
        f"{root}/candidate-summary.json",
        f"{root}/control-identity.json",
        *(f"{root}/seeds/{seed}.json" for seed in SEEDS),
        f"{root}/training.json",
        *common,
    ]


def plan(options: argparse.Namespace) -> None:
    authority_record = json.loads(options.authority.read_text(encoding="utf-8"))
    manifest = json.loads((options.asset_root / "asset-manifest.json").read_text(encoding="utf-8"))
    contract = json.loads((options.asset_root / "portfolio-contract.json").read_text(encoding="utf-8"))
    execution = contract["execution"]
    expected_execution = {
        "attempts_per_role": 1,
        "control_predecessor_minutes": 30,
        "distributed_training": False,
        "gpus_per_role": 1,
        "portfolio_role_count": 10,
        "portfolio_role_minutes_each": 90,
        "portfolio_roles_concurrent": True,
        "recovery_minutes": 5,
        "total_gpu_minute_ceiling": 935,
    }
    for field, expected in expected_execution.items():
        if execution.get(field) != expected:
            raise RuntimeError(f"portfolio execution contract drift: {field}")
    if contract["controls"].get("materialization_role") != "control-materialization":
        raise RuntimeError("portfolio control-materialization role drift")
    evidence_layout = contract["evidence_layout"]
    if evidence_layout.get("control_root") != "results/control-materialization":
        raise RuntimeError("portfolio control evidence root drift")
    expected_control_files = {
        "calendar-preflight.json",
        "control-identity.json",
        "control-summary.json",
        "evidence.json",
        "supervisor.json",
    }
    expected_candidate_files = {
        "calendar-preflight.json",
        "candidate-summary.json",
        "control-identity.json",
        "evidence.json",
        "supervisor.json",
        "training.json",
    }
    if set(evidence_layout.get("control_files", [])) != expected_control_files:
        raise RuntimeError("portfolio control evidence allowlist drift")
    if set(evidence_layout.get("candidate_files", [])) != expected_candidate_files:
        raise RuntimeError("portfolio candidate evidence allowlist drift")
    if tuple(evidence_layout.get("candidate_seed_files_required", [])) != tuple(
        f"seeds/{seed}.json" for seed in SEEDS
    ):
        raise RuntimeError("portfolio candidate seed evidence drift")
    executable = {
        name
        for name in manifest["assets"]
        if name.endswith((".py", ".sh"))
    }
    external = {"runtime.tar.gz", "wheelhouse.tar", "requirements.lock", "corpus.tar"}
    assets = []
    for name, identity in sorted(manifest["assets"].items()):
        item = {
            **identity,
            "license_provenance": "repository license or canonical redistributable manifest",
            "local_path": str((options.asset_root / name).resolve()),
            "logical_name": name,
            "source_class": "external-redistributable" if name in external else "repository-owned",
            "target_platform": "linux-x86_64-glibc",
        }
        if name in executable:
            item["executable"] = True
        assets.append(item)

    jobs = [
        {
            "cpus": 8,
            "expected_exit_code": 0,
            "gate_receipt": "results/control-materialization/evidence.json",
            "gpus": 1,
            "gres": "gpu:l40:1",
            "max_attempts": 1,
            "memory_mb": 65536,
            "partition": "gpu-icrews",
            "retry_on": [],
            "role": contract["controls"]["materialization_role"],
            "script": "job-control-materialization.sh",
            "time_limit_minutes": execution["control_predecessor_minutes"],
        }
    ]
    expected_roles = {
        (candidate_id, capacity): f"{short_name}-{capacity.lower()}"
        for short_name, candidate_id in CANDIDATES
        for capacity in CAPACITIES
    }
    contract_roles = {
        (item["architecture"], item["capacity"]): item["role_id"]
        for item in contract["roles"]
    }
    if contract_roles != expected_roles:
        raise RuntimeError("portfolio contract role matrix differs from operational wrappers")
    roles = [contract["controls"]["materialization_role"]]
    for item in contract["roles"]:
        role = item["role_id"]
        roles.append(role)
        jobs.append(
            {
                "cpus": 8,
                "expected_exit_code": 0,
                "gate_receipt": f"results/{role}/evidence.json",
                "gpus": 1,
                "gres": "gpu:l40:1",
                "max_attempts": 1,
                "memory_mb": 65536,
                "partition": "gpu-icrews",
                "retry_on": [],
                "role": role,
                "script": f"job-{role}.sh",
                "time_limit_minutes": execution["portfolio_role_minutes_each"],
            }
        )

    evidence = [
        "recovery.json",
        "slurm/toolkit-recovery.0.err",
        "slurm/toolkit-recovery.0.out",
    ]
    for role in roles:
        evidence.extend(evidence_for_role(role))

    remote_root = f"{REMOTE_BASE}/runs/{RUN_ID}"
    value = {
        "assets": assets,
        "authority_id": AUTHORITY_ID,
        "authority_revision_sha256": authority_record["authority_revision_sha256"],
        "confirmation_classification": "development-only",
        "deterministic_cuda": True,
        "evidence_allowlist": evidence,
        "evidence_replacements": [
            {"kind": "path", "token": "<REMOTE_RUN_ROOT>", "value": remote_root},
            {"kind": "identity", "token": "<IDENTITY_1>", "value": "rogerlew.ui"},
        ],
        "job_local_capacity": {
            "checkpoint_bytes": 2147483648,
            "expanded_asset_bytes": 8589934592,
            "margin_bytes": 2147483648,
            "minimum_free_bytes": 12884901888,
            "product_bytes": 1073741824,
            "required_inodes": 16000,
        },
        "job_local_cleanup": "toolkit_recoverable",
        "jobs": jobs,
        "package_id": PACKAGE_ID,
        "providers": [
            "research/a10/lemhi_toolkit/providers/transport-scp-v2.json",
            "research/a10/lemhi_toolkit/providers/scheduler-slurm-v2.json",
            "research/a10/lemhi_toolkit/providers/storage-ceph-v2.json",
            "research/a10/lemhi_toolkit/providers/accelerator-l40-v2.json",
            "research/a10/lemhi_toolkit/providers/runtime-cpython311-portable-v2.json",
            "research/a10/lemhi_toolkit/providers/framework-pytorch271-cu128-numpy226-v2.json",
            "research/a10/lemhi_toolkit/providers/toolchain-rust192-linux-x86_64-v2.json",
        ],
        "recovery_contingency": {
            "ambiguity": "retain-reserve",
            "cpus": 2,
            "exact_node_only": True,
            "gate_receipt": "recovery.json",
            "gpu_minutes": execution["recovery_minutes"],
            "gpus": 1,
            "gres": "gpu:l40:1",
            "max_attempts": 1,
            "memory_mb": 1024,
            "partition": "gpu-icrews",
            "script": "recover-job-local-v2.sh",
            "time_limit_minutes": execution["recovery_minutes"],
        },
        "remote_run_root": f"runs/{RUN_ID}",
        "required_capability_scope": "login",
        "required_job_environment": {
            "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
            "PATH": "/registered/run/runtime/bin:/usr/bin:/bin",
            "PYTHONNOUSERSITE": "1",
            "TMPDIR": "/registered/job-local/attempt/tmp",
        },
        "resource_budget_id": BUDGET_ID,
        "run_id": RUN_ID,
        "scheduler_authority_token": AUTHORITY_TOKEN,
        "source_commit": options.source_commit,
        "stop_rules": {
            "ambiguity": "stop",
            "gate_failure": "authorized-retry-only",
            "resource_ceiling": "stop",
        },
        "submission_mode": "operator-explicit",
        "target_platform": "linux-x86_64-glibc",
    }
    write(options.output, value)


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    make_authority = commands.add_parser("authority")
    make_authority.add_argument("--asset-root", type=Path, required=True)
    make_authority.add_argument("--state-root", type=Path, required=True)
    make_authority.add_argument("--source-commit", required=True)
    make_authority.add_argument("--output", type=Path, required=True)
    make_plan = commands.add_parser("plan")
    make_plan.add_argument("--asset-root", type=Path, required=True)
    make_plan.add_argument("--authority", type=Path, required=True)
    make_plan.add_argument("--source-commit", required=True)
    make_plan.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    (authority if options.command == "authority" else plan)(options)


if __name__ == "__main__":
    main()
