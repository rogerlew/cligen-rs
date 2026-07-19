#!/usr/bin/env python3
"""Build private A10M5O2D1 authority input and plan records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REMOTE_BASE = "/ceph/home/rogerlew.ui/.cligen-rs-a10"
PACKAGE_ID = "a10m5o2d1-l40-interconnect-diagnostic"
RUN_ID = "a10m5o2d1-l40-topology-r0"
AUTHORITY_ID = "a10m5o2d1-l40-topology-authority"
BUDGET_ID = "a10m5o2d1-l40-topology-budget"
AUTHORITY_TOKEN = "a10m5o2d1-l40-topology-authority-token"


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)


def authority(options: argparse.Namespace) -> None:
    write(
        options.output,
        {
            "allowed_roots": [str(options.asset_root.resolve())],
            "authority_id": AUTHORITY_ID,
            "confirmation_classification": "development-only",
            "genesis_authorized": True,
            "ledger_anchor": str(options.state_root.resolve() / "authorities" / BUDGET_ID / "ledger.json"),
            "package_id": PACKAGE_ID,
            "predecessor_evidence": [],
            "published_source_commits": [options.source_commit],
            "push_target": "main",
            "resource_budget_id": BUDGET_ID,
            "resource_ceiling_gpu_minutes": 45,
            "resource_class": "single-node-four-l40-topology",
            "scheduler_authority_token": AUTHORITY_TOKEN,
            "scheduler_evidence": [],
            "source_commit": options.source_commit,
            "starting_branch": "main",
        },
    )


def plan(options: argparse.Namespace) -> None:
    authority_record = json.loads(options.authority.read_text(encoding="utf-8"))
    manifest = json.loads((options.asset_root / "asset-manifest.json").read_text(encoding="utf-8"))
    executable = {
        "interconnect.py", "merge_results.py", "run-diagnostic.sh", "job-common.sh",
        "job-interconnect-diagnostic.sh", "recover-job-local-v2.sh", "supervise-v2.sh",
    }
    assets = []
    for name, identity in sorted(manifest["assets"].items()):
        item = {
            **identity,
            "license_provenance": "repository license or canonical redistributable manifest",
            "local_path": str((options.asset_root / name).resolve()),
            "logical_name": name,
            "source_class": "external-redistributable" if name in {"runtime.tar.gz", "wheelhouse.tar", "requirements.lock"} else "repository-owned",
            "target_platform": "linux-x86_64-glibc",
        }
        if name in executable:
            item["executable"] = True
        assets.append(item)
    remote_root = f"{REMOTE_BASE}/runs/{RUN_ID}"
    write(
        options.output,
        {
            "assets": assets,
            "authority_id": AUTHORITY_ID,
            "authority_revision_sha256": authority_record["authority_revision_sha256"],
            "confirmation_classification": "development-only",
            "deterministic_cuda": True,
            "evidence_allowlist": [
                "recovery.json",
                "results/interconnect-diagnostic/evidence.json",
                "slurm/interconnect-diagnostic.0.out",
                "slurm/interconnect-diagnostic.0.err",
                "slurm/toolkit-recovery.0.out",
                "slurm/toolkit-recovery.0.err",
            ],
            "evidence_replacements": [
                {"kind": "path", "token": "<REMOTE_RUN_ROOT>", "value": remote_root},
                {"kind": "identity", "token": "<IDENTITY_1>", "value": "rogerlew.ui"},
            ],
            "job_local_capacity": {
                "checkpoint_bytes": 0,
                "expanded_asset_bytes": 6442450944,
                "margin_bytes": 1073741824,
                "minimum_free_bytes": 10737418240,
                "product_bytes": 104857600,
                "required_inodes": 10000,
            },
            "job_local_cleanup": "toolkit_recoverable",
            "jobs": [{
                "cpus": 16,
                "expected_exit_code": 0,
                "gate_receipt": "results/interconnect-diagnostic/evidence.json",
                "gpus": 4,
                "gres": "gpu:l40:4",
                "max_attempts": 1,
                "memory_mb": 65536,
                "partition": "gpu-icrews",
                "retry_on": [],
                "role": "interconnect-diagnostic",
                "script": "job-interconnect-diagnostic.sh",
                "time_limit_minutes": 10,
            }],
            "package_id": PACKAGE_ID,
            "providers": [
                "research/a10/lemhi_toolkit/providers/transport-scp-v2.json",
                "research/a10/lemhi_toolkit/providers/scheduler-slurm-v2.json",
                "research/a10/lemhi_toolkit/providers/storage-ceph-v2.json",
                "research/a10/lemhi_toolkit/providers/accelerator-l40-multigpu-v1.json",
                "research/a10/lemhi_toolkit/providers/runtime-cpython311-portable-v2.json",
                "research/a10/lemhi_toolkit/providers/framework-pytorch271-cu128-numpy226-v2.json",
                "research/a10/lemhi_toolkit/providers/toolchain-rust192-linux-x86_64-v2.json",
            ],
            "recovery_contingency": {
                "ambiguity": "retain-reserve", "cpus": 2, "exact_node_only": True,
                "gate_receipt": "recovery.json", "gpu_minutes": 5, "gpus": 1,
                "gres": "gpu:l40:1", "max_attempts": 1, "memory_mb": 1024,
                "partition": "gpu-icrews", "script": "recover-job-local-v2.sh",
                "time_limit_minutes": 5,
            },
            "remote_run_root": f"runs/{RUN_ID}",
            "required_capability_scope": "login",
            "required_job_environment": {
                "CUBLAS_WORKSPACE_CONFIG": ":4096:8", "PATH": "/registered/run/runtime/bin:/usr/bin:/bin",
                "PYTHONNOUSERSITE": "1", "TMPDIR": "/registered/job-local/attempt/tmp",
            },
            "resource_budget_id": BUDGET_ID,
            "run_id": RUN_ID,
            "scheduler_authority_token": AUTHORITY_TOKEN,
            "source_commit": options.source_commit,
            "stop_rules": {"ambiguity": "stop", "gate_failure": "authorized-retry-only", "resource_ceiling": "stop"},
            "submission_mode": "operator-explicit",
            "target_platform": "linux-x86_64-glibc",
        },
    )


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
