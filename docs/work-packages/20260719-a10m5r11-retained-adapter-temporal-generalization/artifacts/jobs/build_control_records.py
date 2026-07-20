#!/usr/bin/env python3
"""Build private A10M5R11 authority and plan records."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

REMOTE_BASE = "/ceph/home/rogerlew.ui/.cligen-rs-a10"
PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PACKAGE_ID = "20260719-a10m5r11-retained-adapter-temporal-generalization"
RUN_ID = "a10m5r11-retained-adapter-temporal-generalization-r0"
AUTHORITY_ID = "a10m5r11-retained-adapter-temporal-generalization-authority"
BUDGET_ID = "a10m5r11-retained-adapter-temporal-generalization-budget"
AUTHORITY_TOKEN = "a10m5r11-retained-adapter-temporal-generalization-authority-token"
TOOLKIT_HARDENING_COMMIT = "0ddffd9ac5db2440f74f54285e0df1c2ac856c98"
PREDECESSOR_COMMIT = "dd5db4602ad3ee741707614ec86c26be390490f9"
ROLES = (
    ("annual-monthly-residual-adapter-k1", "annual_monthly_residual_adapter", "K1"),
    ("monthly-residual-adapter-k2", "monthly_residual_adapter", "K2"),
    ("annual-monthly-residual-adapter-k2", "annual_monthly_residual_adapter", "K2"),
)
SEEDS = (147031, 271828, 314159)
REQUIRED_JOB_ENVIRONMENT = {
    "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
    "PATH": "/registered/run/runtime/bin:/usr/bin:/bin",
    "PIP_CACHE_DIR": "/registered/job-local/attempt/pip-cache",
    "PYTHONNOUSERSITE": "1",
    "TMPDIR": "/registered/job-local/attempt/tmp",
    "TORCH_HOME": "/registered/job-local/attempt/torch-cache",
    "XDG_CACHE_HOME": "/registered/job-local/attempt/cache",
}
PREDECESSOR_FILES = (
    "docs/work-packages/20260719-a10m5r10r1r4-science-environment-closure-remedy/artifacts/portfolio-decision.json",
    "docs/work-packages/20260719-a10m5r10r1r4-science-environment-closure-remedy/artifacts/operational-summary.json",
    "docs/work-packages/20260719-a10m5r10r1r4-science-environment-closure-remedy/artifacts/execution-disposition.md",
    "docs/work-packages/20260719-a10m5r10r1r4-science-environment-closure-remedy/artifacts/cleanup-record.json",
    "docs/work-packages/20260719-a10m5r10r1r4-science-environment-closure-remedy/artifacts/review.md",
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    path.chmod(0o600)


def verify_commit(commit: str) -> None:
    subprocess.run(("git", "merge-base", "--is-ancestor", commit, "HEAD"), cwd=REPO, check=True)


def predecessor_bundle() -> dict[str, object]:
    verify_commit(PREDECESSOR_COMMIT)
    files = {}
    for relative in PREDECESSOR_FILES:
        path = REPO / relative
        payload = subprocess.run(
            ("git", "show", f"{PREDECESSOR_COMMIT}:{relative}"),
            cwd=REPO, check=True, capture_output=True,
        ).stdout
        if path.read_bytes() != payload:
            raise RuntimeError(f"predecessor evidence differs from record commit: {relative}")
        files[relative] = {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
    decision = json.loads((REPO / PREDECESSOR_FILES[0]).read_text(encoding="utf-8"))
    if decision.get("terminal") != "A10M5R10-PORTFOLIO-READY" or decision.get("retained_configuration_ids") != [
        "annual_monthly_residual_adapter-k1",
        "monthly_residual_adapter-k2",
        "annual_monthly_residual_adapter-k2",
    ]:
        raise RuntimeError("predecessor retained portfolio semantics drift")
    return {"package_id": "20260719-a10m5r10r1r4-science-environment-closure-remedy", "record_commit": PREDECESSOR_COMMIT, "files": files}


def toolkit_ancestry(source_commit: str) -> dict[str, object]:
    verify_commit(TOOLKIT_HARDENING_COMMIT)
    verify_commit(source_commit)
    return {
        "hardening_commit": TOOLKIT_HARDENING_COMMIT,
        "hardening_commit_is_ancestor": True,
        "source_commit": source_commit,
    }


def verify_assets(root: Path, source_commit: str) -> dict[str, object]:
    manifest = json.loads((root / "asset-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("package_id") != PACKAGE_ID or manifest.get("source_commit") != source_commit:
        raise RuntimeError("asset package/source identity drift")
    for name, expected in manifest["assets"].items():
        path = root / name
        if {"bytes": path.stat().st_size, "sha256": digest(path)} != expected:
            raise RuntimeError(f"asset identity drift: {name}")
    spec = importlib.util.spec_from_file_location("layout", PACKAGE / "artifacts/verify_corpus_layout.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load corpus verifier")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    pin = verifier.load_pin(PACKAGE / "artifacts/corpus-layout-pin.json")
    if verifier.identity(root / "corpus.tar") != pin["archive"] or verifier.inspect_layout(root / "corpus.tar") != pin["layout"]:
        raise RuntimeError("corpus identity/layout drift")
    return manifest


def authority(options: argparse.Namespace) -> None:
    verify_assets(options.asset_root, options.source_commit)
    value = {
        "allowed_roots": [str(options.asset_root.resolve())],
        "authority_id": AUTHORITY_ID,
        "confirmation_classification": "development-only",
        "genesis_authorized": True,
        "ledger_anchor": str(options.state_root.resolve() / "authorities" / BUDGET_ID / "ledger.json"),
        "package_id": PACKAGE_ID,
        "predecessor_evidence": [],
        "predecessor_package_evidence": predecessor_bundle(),
        "published_source_commits": [options.source_commit],
        "push_target": "main",
        "resource_budget_id": BUDGET_ID,
        "resource_ceiling_gpu_minutes": 305,
        "resource_class": "one-l40-retained-adapter-temporal",
        "scheduler_authority_token": AUTHORITY_TOKEN,
        "scheduler_evidence": [],
        "source_commit": options.source_commit,
        "starting_branch": "main",
        "toolkit_hardening_proof": toolkit_ancestry(options.source_commit),
    }
    write(options.output, value)


def evidence(role: str) -> list[str]:
    root = f"results/{role}"
    common = [
        f"admissions/{role}.json", f"{root}/evidence.json", f"{root}/setup.json",
        f"{root}/setup.log", f"{root}/supervisor.json", f"slurm/{role}.0.err",
        f"slurm/{role}.0.out",
    ]
    if role == "control-materialization":
        return [f"{root}/calendar-preflight.json", f"{root}/control-identity.json", f"{root}/control-summary.json", *common]
    return [
        f"{root}/calendar-preflight.json", f"{root}/candidate-summary.json",
        f"{root}/control-identity.json", f"{root}/streams.json",
        *(f"{root}/seeds/{seed}.json" for seed in SEEDS), f"{root}/training.json", *common,
    ]


def plan(options: argparse.Namespace) -> None:
    manifest = verify_assets(options.asset_root, options.source_commit)
    authority_record = json.loads(options.authority.read_text(encoding="utf-8"))
    temporal = json.loads((options.asset_root / "temporal-contract.json").read_text(encoding="utf-8"))
    expected = {(role, candidate, capacity) for role, candidate, capacity in ROLES}
    actual = {(row["role_id"], row["architecture"], row["capacity"]) for row in temporal["roles"]}
    if actual != expected or authority_record.get("predecessor_package_evidence") != predecessor_bundle():
        raise RuntimeError("authority or temporal matrix drift")
    executable = {name for name in manifest["assets"] if name.endswith((".py", ".sh"))}
    external = {"runtime.tar.gz", "wheelhouse.tar", "requirements.lock", "corpus.tar"}
    assets = []
    for name, item_identity in sorted(manifest["assets"].items()):
        row = {
            **item_identity, "license_provenance": "repository license or canonical redistributable manifest",
            "local_path": str((options.asset_root / name).resolve()), "logical_name": name,
            "source_class": "external-redistributable" if name in external else "repository-owned",
            "target_platform": "linux-x86_64-glibc",
        }
        if name in executable:
            row["executable"] = True
        assets.append(row)
    manifest_path = (options.asset_root / "asset-manifest.json").resolve()
    assets.append({
        "bytes": manifest_path.stat().st_size, "sha256": digest(manifest_path),
        "license_provenance": "repository-owned execution manifest", "local_path": str(manifest_path),
        "logical_name": "asset-manifest.json", "source_class": "repository-owned",
        "target_platform": "linux-x86_64-glibc",
    })
    jobs = [{
        "cpus": 8, "expected_exit_code": 0, "gate_receipt": "results/control-materialization/evidence.json",
        "gpus": 1, "gres": "gpu:l40:1", "max_attempts": 1, "memory_mb": 65536,
        "partition": "gpu-icrews", "retry_on": [], "role": "control-materialization",
        "script": "job-control-materialization.sh", "time_limit_minutes": 30,
    }]
    for role, _, _ in ROLES:
        jobs.append({
            "cpus": 8, "expected_exit_code": 0, "gate_receipt": f"results/{role}/evidence.json",
            "gpus": 1, "gres": "gpu:l40:1", "max_attempts": 1, "memory_mb": 65536,
            "partition": "gpu-icrews", "retry_on": [], "role": role,
            "script": f"job-{role}.sh", "time_limit_minutes": 90,
        })
    allowlist = ["recovery.json", "slurm/toolkit-recovery.0.err", "slurm/toolkit-recovery.0.out"]
    for role in ("control-materialization", *(row[0] for row in ROLES)):
        allowlist.extend(evidence(role))
    remote_root = f"{REMOTE_BASE}/runs/{RUN_ID}"
    value = {
        "assets": assets, "authority_id": AUTHORITY_ID,
        "authority_revision_sha256": authority_record["authority_revision_sha256"],
        "confirmation_classification": "development-only", "deterministic_cuda": True,
        "evidence_allowlist": allowlist,
        "evidence_replacements": [
            {"kind": "path", "token": "<REMOTE_RUN_ROOT>", "value": remote_root},
            {"kind": "identity", "token": "<IDENTITY_1>", "value": "rogerlew.ui"},
        ],
        "job_local_capacity": {"checkpoint_bytes": 2147483648, "expanded_asset_bytes": 11811160064, "margin_bytes": 2147483648, "minimum_free_bytes": 17179869184, "product_bytes": 1073741824, "required_inodes": 16000},
        "job_local_cleanup": "toolkit_recoverable", "jobs": jobs, "package_id": PACKAGE_ID,
        "predecessor_package_evidence": predecessor_bundle(),
        "providers": [
            "research/a10/lemhi_toolkit/providers/transport-scp-v2.json",
            "research/a10/lemhi_toolkit/providers/scheduler-slurm-v2.json",
            "research/a10/lemhi_toolkit/providers/storage-ceph-v2.json",
            "research/a10/lemhi_toolkit/providers/accelerator-l40-v2.json",
            "research/a10/lemhi_toolkit/providers/runtime-cpython311-portable-v2.json",
            "research/a10/lemhi_toolkit/providers/framework-pytorch271-cu128-numpy226-v2.json",
            "research/a10/lemhi_toolkit/providers/toolchain-rust192-linux-x86_64-v2.json"
        ],
        "recovery_contingency": {"ambiguity": "retain-reserve", "cpus": 2, "exact_node_only": True, "gate_receipt": "recovery.json", "gpu_minutes": 5, "gpus": 1, "gres": "gpu:l40:1", "max_attempts": 1, "memory_mb": 1024, "partition": "gpu-icrews", "script": "recover-job-local-v2.sh", "time_limit_minutes": 5},
        "remote_run_root": f"runs/{RUN_ID}", "required_capability_scope": "login",
        "required_job_environment": REQUIRED_JOB_ENVIRONMENT, "resource_budget_id": BUDGET_ID,
        "run_id": RUN_ID, "scheduler_authority_token": AUTHORITY_TOKEN,
        "source_commit": options.source_commit,
        "stop_rules": {"ambiguity": "stop", "gate_failure": "authorized-retry-only", "resource_ceiling": "stop"},
        "submission_mode": "operator-explicit", "target_platform": "linux-x86_64-glibc",
        "toolkit_hardening_proof": toolkit_ancestry(options.source_commit),
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
