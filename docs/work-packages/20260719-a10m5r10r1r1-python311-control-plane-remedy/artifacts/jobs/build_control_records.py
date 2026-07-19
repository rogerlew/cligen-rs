#!/usr/bin/env python3
"""Build private A10M5R10R1R1 authority input and staged portfolio plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

REMOTE_BASE = "/ceph/home/rogerlew.ui/.cligen-rs-a10"
PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PACKAGE_ID = "20260719-a10m5r10r1r1-python311-control-plane-remedy"
RUN_ID = "a10m5r10r1r1-python311-control-plane-remedy-r0"
AUTHORITY_ID = "a10m5r10r1r1-python311-control-plane-remedy-authority"
BUDGET_ID = "a10m5r10r1r1-python311-control-plane-remedy-budget"
AUTHORITY_TOKEN = "a10m5r10r1r1-python311-control-plane-remedy-authority-token"
TOOLKIT_HARDENING_COMMIT = "0ddffd9ac5db2440f74f54285e0df1c2ac856c98"
PREDECESSOR_MANIFEST = PACKAGE / "artifacts/predecessor-evidence-identities.json"
PREDECESSOR_MANIFEST_BYTES = 2946
PREDECESSOR_MANIFEST_SHA256 = (
    "f9f559d4ae5c12d66f7254b41339bb2ebaf8846620202e164e83191c3a0c26f5"
)
HARDENED_TOOLKIT_PATHS = (
    "research/a10/lemhi_toolkit/adapters.py",
    "research/a10/lemhi_toolkit/cli.py",
    "research/a10/lemhi_toolkit/core.py",
    "research/a10/lemhi_toolkit/remote/pack_evidence.sh",
)

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


def file_identity(
    path: Path, expected_sha256: str, expected_bytes: int | None = None
) -> dict[str, object]:
    if HEX64.fullmatch(expected_sha256) is None:
        raise RuntimeError("predecessor file SHA-256 must be 64 lowercase hex")
    actual_sha256 = digest(path)
    if actual_sha256 != expected_sha256:
        raise RuntimeError("predecessor file SHA-256 mismatch")
    if expected_bytes is not None and path.stat().st_size != expected_bytes:
        raise RuntimeError("predecessor file byte count mismatch")
    return {
        "bytes": path.stat().st_size,
        "local_path": str(path.resolve()),
        "sha256": actual_sha256,
    }


def predecessor_bundle() -> dict[str, object]:
    manifest_identity = file_identity(
        PREDECESSOR_MANIFEST,
        PREDECESSOR_MANIFEST_SHA256,
        PREDECESSOR_MANIFEST_BYTES,
    )
    document = json.loads(PREDECESSOR_MANIFEST.read_text(encoding="utf-8"))
    if (
        document.get("schema_version") != 1
        or document.get("package_id") != PACKAGE_ID
        or set(document.get("predecessors", {}))
        != {"a10m5r10r1_operational_hold", "a10m5o1r2_toolkit_hardening"}
    ):
        raise RuntimeError("predecessor identity manifest semantic drift")
    bound: dict[str, object] = {}
    repo_root = REPO.resolve()
    for predecessor_name, predecessor in document["predecessors"].items():
        files: dict[str, object] = {}
        for name, expected in predecessor["files"].items():
            path = (REPO / expected["source_path"]).resolve()
            if not path.is_relative_to(repo_root):
                raise RuntimeError(f"predecessor source escapes repository: {name}")
            files[name] = file_identity(
                path, expected["sha256"], expected["bytes"]
            )
        bound[predecessor_name] = {
            **{key: value for key, value in predecessor.items() if key != "files"},
            "files": files,
        }

    r1 = bound["a10m5r10r1_operational_hold"]
    r1_summary_path = Path(r1["files"]["operational-summary.json"]["local_path"])
    r1_summary = json.loads(r1_summary_path.read_text(encoding="utf-8"))
    r1_cleanup_path = Path(r1["files"]["cleanup-record.json"]["local_path"])
    r1_cleanup = json.loads(r1_cleanup_path.read_text(encoding="utf-8"))
    if (
        r1_summary.get("package_id") != r1["package_id"]
        or r1_summary.get("run_id") != r1["run_id"]
        or r1_summary.get("terminal") != r1["terminal"]
        or r1_summary.get("science", {}).get(
            "architecture_interpretation_authorized"
        )
        is not False
        or r1_cleanup.get("remote_absent") is not True
        or r1_cleanup.get("package_id") != r1["package_id"]
        or r1_cleanup.get("run_id") != r1["run_id"]
    ):
        raise RuntimeError("R1 operational HOLD semantic drift")

    hardening = bound["a10m5o1r2_toolkit_hardening"]
    disposition_path = Path(
        hardening["files"]["execution-disposition.md"]["local_path"]
    )
    if hardening["terminal"] not in disposition_path.read_text(encoding="utf-8"):
        raise RuntimeError("A10M5O1R2 hardening disposition semantic drift")
    return {"identity_manifest": manifest_identity, "predecessors": bound}


def toolkit_ancestry(source_commit: str) -> dict[str, object]:
    commands = (
        ("merge-base", "--is-ancestor", TOOLKIT_HARDENING_COMMIT, source_commit),
        (
            "diff",
            "--quiet",
            TOOLKIT_HARDENING_COMMIT,
            source_commit,
            "--",
            *HARDENED_TOOLKIT_PATHS,
        ),
    )
    for command in commands:
        result = subprocess.run(
            ("git", *command), cwd=REPO, check=False, capture_output=True
        )
        if result.returncode != 0:
            raise RuntimeError(f"toolkit ancestry/diff proof failed: {' '.join(command)}")
    return {
        "diff_from_hardening_commit_empty": True,
        "hardening_commit": TOOLKIT_HARDENING_COMMIT,
        "hardening_commit_is_ancestor": True,
        "protected_paths": list(HARDENED_TOOLKIT_PATHS),
        "source_commit": source_commit,
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
    predecessor = predecessor_bundle()
    toolkit_proof = toolkit_ancestry(options.source_commit)
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
        "predecessor_package_evidence": predecessor,
        "published_source_commits": [options.source_commit],
        "push_target": "main",
        "resource_budget_id": BUDGET_ID,
        "resource_ceiling_gpu_minutes": ceiling,
        "resource_class": "one-l40-staged-parallel-architecture-portfolio",
        "scheduler_authority_token": AUTHORITY_TOKEN,
        "scheduler_evidence": [],
        "source_commit": options.source_commit,
        "starting_branch": "main",
        "toolkit_hardening_proof": toolkit_proof,
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
    predecessor = authority_record.get("predecessor_package_evidence")
    expected_predecessor = predecessor_bundle()
    if predecessor != expected_predecessor:
        raise RuntimeError("initialized authority lacks exact predecessor evidence")
    toolkit_proof = authority_record.get("toolkit_hardening_proof")
    if toolkit_proof != toolkit_ancestry(options.source_commit):
        raise RuntimeError("initialized authority lacks toolkit ancestry/diff proof")
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
        "predecessor_package_evidence": predecessor,
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
        "toolkit_hardening_proof": toolkit_proof,
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
