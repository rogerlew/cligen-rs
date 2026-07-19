#!/usr/bin/env python3
"""Build private A10M5R10R1 authority input and staged portfolio plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

REMOTE_BASE = "/ceph/home/rogerlew.ui/.cligen-rs-a10"
PACKAGE_ID = "20260719-a10m5r10r1-candidate-job-local-capacity-remedy"
RUN_ID = "a10m5r10r1-candidate-job-local-capacity-remedy-r0"
AUTHORITY_ID = "a10m5r10r1-candidate-job-local-capacity-remedy-authority"
BUDGET_ID = "a10m5r10r1-candidate-job-local-capacity-remedy-budget"
AUTHORITY_TOKEN = "a10m5r10r1-candidate-job-local-capacity-remedy-authority-token"

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
HEX64 = re.compile(r"[0-9a-f]{64}")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def file_identity(path: Path, expected_sha256: str) -> dict[str, object]:
    if HEX64.fullmatch(expected_sha256) is None:
        raise RuntimeError("R0 predecessor file SHA-256 must be 64 lowercase hex")
    actual_sha256 = digest(path)
    if actual_sha256 != expected_sha256:
        raise RuntimeError("R0 predecessor file SHA-256 mismatch")
    return {
        "bytes": path.stat().st_size,
        "local_path": str(path.resolve()),
        "sha256": actual_sha256,
    }


def toolkit_predecessor_identity(
    path: Path, expected_sha256: str, record_type: str
) -> dict[str, object]:
    result = file_identity(path, expected_sha256)
    receipt = json.loads(path.read_text(encoding="utf-8"))
    recorded = receipt.get("record_sha256")
    semantic = dict(receipt)
    semantic.pop("record_sha256", None)
    authenticated = (
        isinstance(recorded, str)
        and HEX64.fullmatch(recorded) is not None
        and recorded == hashlib.sha256(canonical(semantic)).hexdigest()
    )
    if not authenticated:
        raise RuntimeError("R0 predecessor receipt record identity invalid")
    if (
        receipt.get("package_id")
        != "20260719-a10m5r10-parallel-architecture-portfolio"
        or receipt.get("run_id") != "a10m5r10-parallel-architecture-portfolio-r0"
        or receipt.get("record_type") != record_type
    ):
        raise RuntimeError(f"R0 predecessor {record_type} identity mismatch")
    if record_type == "terminal_receipt" and receipt.get("terminal") != (
        "LEMHI-TOOLKIT-RUN-CLOSED"
    ):
        raise RuntimeError("R0 predecessor toolkit run is not closed")
    if record_type == "cleanup_receipt" and (
        receipt.get("job_local_cleanup") != "verified_absent"
        or receipt.get("remote_absent") is not True
    ):
        raise RuntimeError("R0 predecessor cleanup is incomplete")
    result["record_sha256"] = recorded
    return result


def predecessor_bundle(options: argparse.Namespace) -> dict[str, object]:
    summary_identity = file_identity(
        options.predecessor_r0_operational_summary,
        options.predecessor_r0_operational_summary_sha256,
    )
    summary = json.loads(
        options.predecessor_r0_operational_summary.read_text(encoding="utf-8")
    )
    if (
        summary.get("package_id")
        != "20260719-a10m5r10-parallel-architecture-portfolio"
        or summary.get("run_id") != "a10m5r10-parallel-architecture-portfolio-r0"
        or summary.get("terminal") != "HOLD-A10M5R10-JOB-LOCAL-CAPACITY"
        or summary.get("science", {}).get("scientific_interpretation_authorized")
        is not False
    ):
        raise RuntimeError("R0 operational summary identity mismatch")
    return {
        "operational_summary": summary_identity,
        "resource_ledger": file_identity(
            options.predecessor_r0_resource_ledger,
            options.predecessor_r0_resource_ledger_sha256,
        ),
        "terminal_receipt": toolkit_predecessor_identity(
            options.predecessor_r0_terminal,
            options.predecessor_r0_terminal_sha256,
            "terminal_receipt",
        ),
        "cleanup_receipt": toolkit_predecessor_identity(
            options.predecessor_r0_cleanup,
            options.predecessor_r0_cleanup_sha256,
            "cleanup_receipt",
        ),
    }


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)


def authority(options: argparse.Namespace) -> None:
    contract = json.loads(
        (options.asset_root / "job-local-capacity-contract.json").read_text(
            encoding="utf-8"
        )
    )
    ceiling = contract["resources"]["total_gpu_minute_ceiling"]
    if ceiling != 935:
        raise RuntimeError("capacity remedy resource ceiling drift")
    predecessor = predecessor_bundle(options)
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
        "predecessor_r0_evidence": predecessor,
        "published_source_commits": [options.source_commit],
        "push_target": "main",
        "resource_budget_id": BUDGET_ID,
        "resource_ceiling_gpu_minutes": ceiling,
        "resource_class": "one-l40-staged-parallel-architecture-portfolio",
        "scheduler_authority_token": AUTHORITY_TOKEN,
        "scheduler_evidence": [],
        "source_commit": options.source_commit,
        "starting_branch": "main",
    }
    write(options.output, value)


def evidence_for_role(role: str) -> list[str]:
    root = f"results/{role}"
    common = [
        f"admissions/{role}.json",
        f"{root}/evidence.json",
        f"{root}/setup.json",
        f"{root}/setup.log",
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
    manifest = json.loads(
        (options.asset_root / "asset-manifest.json").read_text(encoding="utf-8")
    )
    if (
        manifest.get("package_id") != PACKAGE_ID
        or manifest.get("source_commit") != options.source_commit
    ):
        raise RuntimeError("asset manifest package/source identity drift")
    portfolio = json.loads(
        (options.asset_root / "portfolio-contract.json").read_text(encoding="utf-8")
    )
    remedy = json.loads(
        (options.asset_root / "job-local-capacity-contract.json").read_text(
            encoding="utf-8"
        )
    )
    resources = remedy["resources"]
    predecessor = authority_record.get("predecessor_r0_evidence")
    if not isinstance(predecessor, dict) or set(predecessor) != {
        "cleanup_receipt",
        "operational_summary",
        "resource_ledger",
        "terminal_receipt",
    }:
        raise RuntimeError("initialized authority lacks bound R0 predecessor evidence")
    for name, item in predecessor.items():
        if not isinstance(item, dict):
            raise RuntimeError(f"malformed R0 predecessor binding: {name}")
        file_identity(Path(str(item["local_path"])), str(item["sha256"]))
    if 30 + resources["candidate_role_count"] * 90 + 5 != 935:
        raise RuntimeError("capacity remedy resource arithmetic drift")
    if resources["attempts_per_role"] != 1:
        raise RuntimeError("capacity remedy attempts drift")
    executable = {
        name for name in manifest["assets"] if name.endswith((".py", ".sh"))
    }
    external = {"runtime.tar.gz", "wheelhouse.tar", "requirements.lock", "corpus.tar"}
    assets = []
    for name, item_identity in sorted(manifest["assets"].items()):
        item = {
            **item_identity,
            "license_provenance": "repository license or canonical redistributable manifest",
            "local_path": str((options.asset_root / name).resolve()),
            "logical_name": name,
            "source_class": "external-redistributable" if name in external else "repository-owned",
            "target_platform": "linux-x86_64-glibc",
        }
        if name in executable:
            item["executable"] = True
        assets.append(item)
    manifest_path = (options.asset_root / "asset-manifest.json").resolve()
    assets.append(
        {
            "bytes": manifest_path.stat().st_size,
            "license_provenance": "repository-owned execution manifest",
            "local_path": str(manifest_path),
            "logical_name": "asset-manifest.json",
            "sha256": digest(manifest_path),
            "source_class": "repository-owned",
            "target_platform": "linux-x86_64-glibc",
        }
    )

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
            "role": "control-materialization",
            "script": "job-control-materialization.sh",
            "time_limit_minutes": resources["control_minutes"],
        }
    ]
    expected_roles = {
        (candidate_id, capacity): f"{short_name}-{capacity.lower()}"
        for short_name, candidate_id in CANDIDATES
        for capacity in CAPACITIES
    }
    portfolio_roles = {
        (item["architecture"], item["capacity"]): item["role_id"]
        for item in portfolio["roles"]
    }
    if portfolio_roles != expected_roles:
        raise RuntimeError("portfolio role matrix differs from successor wrappers")
    roles = ["control-materialization"]
    for item in portfolio["roles"]:
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
                "time_limit_minutes": resources["candidate_minutes_each"],
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
            "expanded_asset_bytes": 11811160064,
            "margin_bytes": 2147483648,
            "minimum_free_bytes": 17179869184,
            "product_bytes": 1073741824,
            "required_inodes": 16000,
        },
        "job_local_cleanup": "toolkit_recoverable",
        "jobs": jobs,
        "package_id": PACKAGE_ID,
        "predecessor_r0_evidence": predecessor,
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
            "gpu_minutes": resources["recovery_minutes"],
            "gpus": 1,
            "gres": "gpu:l40:1",
            "max_attempts": 1,
            "memory_mb": 1024,
            "partition": "gpu-icrews",
            "script": "recover-job-local-v2.sh",
            "time_limit_minutes": resources["recovery_minutes"],
        },
        "remote_run_root": f"runs/{RUN_ID}",
        "required_capability_scope": "login",
        "required_job_environment": {
            "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
            "PATH": "/registered/run/runtime/bin:/usr/bin:/bin",
            "PIP_CACHE_DIR": "/registered/job-local/attempt/pip-cache",
            "PYTHONNOUSERSITE": "1",
            "TMPDIR": "/registered/job-local/attempt/tmp",
            "TORCH_HOME": "/registered/job-local/attempt/torch-cache",
            "XDG_CACHE_HOME": "/registered/job-local/attempt/cache",
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
    make_authority.add_argument(
        "--predecessor-r0-operational-summary", type=Path, required=True
    )
    make_authority.add_argument(
        "--predecessor-r0-operational-summary-sha256", required=True
    )
    make_authority.add_argument(
        "--predecessor-r0-resource-ledger", type=Path, required=True
    )
    make_authority.add_argument(
        "--predecessor-r0-resource-ledger-sha256", required=True
    )
    make_authority.add_argument("--predecessor-r0-terminal", type=Path, required=True)
    make_authority.add_argument("--predecessor-r0-terminal-sha256", required=True)
    make_authority.add_argument("--predecessor-r0-cleanup", type=Path, required=True)
    make_authority.add_argument("--predecessor-r0-cleanup-sha256", required=True)
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
