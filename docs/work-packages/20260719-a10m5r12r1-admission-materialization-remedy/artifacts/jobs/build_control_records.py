#!/usr/bin/env python3
"""Build private A10M5R12 authority and plan records."""

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
PACKAGE_ID = "20260719-a10m5r12r1-admission-materialization-remedy"
RUN_ID = "a10m5r12r1-admission-materialization-remedy-r0"
AUTHORITY_ID = "a10m5r12r1-admission-materialization-remedy-authority"
BUDGET_ID = "a10m5r12r1-admission-materialization-remedy-budget"
AUTHORITY_TOKEN = "a10m5r12r1-admission-materialization-remedy-authority-token"
TOOLKIT_HARDENING_COMMIT = "614157a3a5013014a4217a21727892f978d3e7b3"
PREDECESSOR_COMMIT = "b3d4e81e5305d584dfe6609f418bc976e64165e0"
ROLES = (
    ("continuous-medium-latent-process-k2", "continuous_medium_latent_process", "K2"),
    ("continuous-hierarchical-latent-process-k2", "continuous_hierarchical_latent_process", "K2"),
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
    "docs/work-packages/20260719-a10m5r11r2-comparator-burn-contract-remedy/artifacts/temporal-result.json",
    "docs/work-packages/20260719-a10m5r11r2-comparator-burn-contract-remedy/artifacts/replay-identity.json",
    "docs/work-packages/20260719-a10m5r11r2-comparator-burn-contract-remedy/artifacts/execution-disposition.md",
    "docs/work-packages/20260719-a10m5r11r2-comparator-burn-contract-remedy/artifacts/gate-results.md",
    "docs/work-packages/20260719-a10m5r11r2-comparator-burn-contract-remedy/artifacts/review.md",
    "docs/work-packages/20260719-a10m5r11r2-comparator-burn-contract-remedy/package.md",
)
OPERATIONAL_PREDECESSOR_FILES = (
    "docs/work-packages/20260719-a10m5r12-continuous-latent-temporal-process/package.md",
    "docs/work-packages/20260719-a10m5r12-continuous-latent-temporal-process/artifacts/execution-disposition.md",
    "docs/work-packages/20260719-a10m5r12-continuous-latent-temporal-process/artifacts/gate-results.md",
    "docs/work-packages/20260719-a10m5r12-continuous-latent-temporal-process/artifacts/review.md",
    "docs/work-packages/20260719-a10m5r12-continuous-latent-temporal-process/artifacts/toolkit-recovered/job-control-materialization.0.json",
    "docs/work-packages/20260719-a10m5r12-continuous-latent-temporal-process/artifacts/toolkit-recovered/collection.json",
    "docs/work-packages/20260719-a10m5r12-continuous-latent-temporal-process/artifacts/toolkit-recovered/cleanup.json",
    "docs/work-packages/20260719-a10m5r12-continuous-latent-temporal-process/artifacts/toolkit-recovered/terminal.json",
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


def authenticated(value: dict[str, object]) -> bool:
    recorded = value.get("record_sha256")
    semantic = dict(value)
    semantic.pop("record_sha256", None)
    payload = json.dumps(
        semantic, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return isinstance(recorded, str) and recorded == hashlib.sha256(
        payload
    ).hexdigest()


def verify_commit(commit: str) -> None:
    subprocess.run(("git", "merge-base", "--is-ancestor", commit, "HEAD"), cwd=REPO, check=True)


def git_bytes(commit: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{relative}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def verify_committed_file(path: Path, commit: str) -> str:
    relative = path.resolve().relative_to(REPO).as_posix()
    if path.read_bytes() != git_bytes(commit, relative):
        raise RuntimeError(f"repository verifier differs from source commit: {relative}")
    return relative


def verify_published_source(commit: str) -> None:
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()
    upstream = subprocess.run(
        ("git", "rev-parse", "origin/main"), cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()
    branch = subprocess.run(
        ("git", "branch", "--show-current"), cwd=REPO, check=True, capture_output=True, text=True
    ).stdout.strip()
    relative = Path(__file__).resolve().relative_to(REPO).as_posix()
    if not (
        commit == head == upstream
        and branch == "main"
        and Path(__file__).read_bytes() == git_bytes(commit, relative)
    ):
        raise RuntimeError("authority source is not the exact published main scaffold")


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
    summary = json.loads((REPO / PREDECESSOR_FILES[0]).read_text(encoding="utf-8"))
    if (
        summary.get("terminal")
        != "HOLD-A10M5R11-NO-TEMPORALLY-ELIGIBLE-CANDIDATE"
        or summary.get("eligible_configurations") != []
        or summary.get("protected_roles_opened") != []
    ):
        raise RuntimeError("predecessor temporal hold semantics drift")
    return {"package_id": "20260719-a10m5r11r2-comparator-burn-contract-remedy", "record_commit": PREDECESSOR_COMMIT, "files": files}


def operational_predecessor_bundle(source_commit: str) -> dict[str, object]:
    files = {}
    for relative in OPERATIONAL_PREDECESSOR_FILES:
        payload = git_bytes(source_commit, relative)
        path = REPO / relative
        if path.read_bytes() != payload:
            raise RuntimeError(
                f"operational predecessor differs from source commit: {relative}"
            )
        files[relative] = {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    job, collection, cleanup, terminal = (
        json.loads((REPO / relative).read_text(encoding="utf-8"))
        for relative in OPERATIONAL_PREDECESSOR_FILES[4:]
    )
    expected_common = {
        "package_id": "20260719-a10m5r12-continuous-latent-temporal-process",
        "run_id": "a10m5r12-continuous-latent-temporal-process-r0",
        "source_commit": "614157a3a5013014a4217a21727892f978d3e7b3",
    }
    if not (
        all(
            authenticated(record)
            and all(record.get(key) == value for key, value in expected_common.items())
            for record in (job, collection, cleanup, terminal)
        )
        and job.get("passed") is False
        and job.get("result", {}).get("actual_gpu_minutes") == 1
        and job.get("result", {}).get("gates", {}).get(
            "submission_admission_authenticated"
        )
        is False
        and job.get("result", {}).get("gates", {}).get("job_local_cleanup")
        is True
        and collection.get("download_promoted") is True
        and collection.get("sanitization_policy")
        == "lemhi-evidence-projection-5"
        and "admissions/control-materialization.json"
        in collection.get("absent", [])
        and cleanup.get("remote_absent") is True
        and cleanup.get("job_local_cleanup") == "verified_absent"
        and terminal.get("terminal") == "LEMHI-TOOLKIT-RUN-CLOSED"
        and terminal.get("attempt_count") == 1
        and terminal.get("stopped_role_count") == 2
        and terminal.get("cleanup")
        == {"job_local_cleanup": "verified_absent", "remote_absent": True}
    ):
        raise RuntimeError("operational predecessor failure semantics drift")
    return {
        "package_id": "20260719-a10m5r12-continuous-latent-temporal-process",
        "record_commit": source_commit,
        "files": files,
    }


def toolkit_ancestry(source_commit: str) -> dict[str, object]:
    verify_commit(TOOLKIT_HARDENING_COMMIT)
    verify_commit(source_commit)
    return {
        "hardening_commit": TOOLKIT_HARDENING_COMMIT,
        "hardening_commit_is_ancestor": True,
        "source_commit": source_commit,
    }


def verify_assets(root: Path, source_commit: str) -> dict[str, object]:
    verify_published_source(source_commit)
    manifest = json.loads((root / "asset-manifest.json").read_text(encoding="utf-8"))
    if manifest.get("package_id") != PACKAGE_ID or manifest.get("source_commit") != source_commit:
        raise RuntimeError("asset package/source identity drift")
    for name, expected in manifest["assets"].items():
        path = root / name
        if {
            "bytes": path.stat().st_size,
            "sha256": digest(path),
        } != {key: expected[key] for key in ("bytes", "sha256")}:
            raise RuntimeError(f"asset identity drift: {name}")
        source_path = expected.get("source_path")
        if source_path is not None:
            payload = git_bytes(source_commit, source_path)
            if len(payload) != path.stat().st_size or hashlib.sha256(payload).hexdigest() != digest(path):
                raise RuntimeError(f"repository asset differs from source commit: {name}")
    configuration = json.loads((root / "canonical-configuration.json").read_text())
    designation = json.loads((root / "canonical-designation-index.json").read_text())
    current = designation["current"]
    if not (
        current["status"] == "current"
        and current["configuration_id"] == configuration["configuration_id"]
        and current["configuration_semantic_sha256"]
        == configuration["configuration_semantic_sha256"]
        == manifest.get("canonical_configuration_semantic_sha256")
        and manifest["assets"]["runtime.tar.gz"]
        == {
            "bytes": configuration["runtime"]["artifact_bytes"],
            "sha256": configuration["runtime"]["artifact_sha256"],
        }
        and manifest["assets"]["wheelhouse.tar"]
        == {
            "bytes": configuration["framework"]["wheelhouse_bytes"],
            "sha256": configuration["framework"]["wheelhouse_sha256"],
        }
        and manifest["assets"]["requirements.lock"]["sha256"]
        == configuration["framework"]["requirements_lock_sha256"]
    ):
        raise RuntimeError("canonical designation/configuration assets drift")
    layout_verifier = PACKAGE / "artifacts/verify_corpus_layout.py"
    verify_committed_file(layout_verifier, source_commit)
    spec = importlib.util.spec_from_file_location("layout", layout_verifier)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load corpus verifier")
    verifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verifier)
    pin = verifier.load_pin(PACKAGE / "artifacts/corpus-layout-pin.json")
    if verifier.identity(root / "corpus.tar") != pin["archive"] or verifier.inspect_layout(root / "corpus.tar") != pin["layout"]:
        raise RuntimeError("corpus identity/layout drift")
    return manifest


def prospective_calendar_preflight(root: Path) -> dict[str, object]:
    path = root / "calendar-preflight.json"
    expected = "58a927b6facc255fb8feb803b05c23be3cb727790fb4dd7ac77f627cffa48c75"
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        digest(path) != expected
        or value.get("valid") is not True
        or value.get("profile_id") != "daymet_official_365_v1"
        or value.get("counts", {}).get("calendar_axis_rows_per_point") != 10958
        or value.get("counts", {}).get("core_observed_rows_per_point") != 10950
        or value.get("window", {}).get("end_semantics") != "exclusive"
        or value.get("month_year_eligibility", {}).get("eligible") is not True
        or value.get("fixture", {}).get("spans_observed_february_29") is not True
        or value.get("fixture", {}).get("spans_absent_leap_december_31") is not True
    ):
        raise RuntimeError("prospective calendar/missingness preflight failed")
    return {"bytes": path.stat().st_size, "sha256": expected, "valid": True}


def authority(options: argparse.Namespace) -> None:
    verify_assets(options.asset_root, options.source_commit)
    calendar_preflight = prospective_calendar_preflight(options.asset_root)
    value = {
        "allowed_roots": [str(options.asset_root.resolve())],
        "authority_id": AUTHORITY_ID,
        "confirmation_classification": "development-only",
        "genesis_authorized": True,
        "ledger_anchor": str(options.state_root.resolve() / "authorities" / BUDGET_ID / "ledger.json"),
        "package_id": PACKAGE_ID,
        "operational_predecessor_package_evidence": operational_predecessor_bundle(
            options.source_commit
        ),
        "predecessor_evidence": [],
        "predecessor_package_evidence": predecessor_bundle(),
        "prospective_calendar_preflight": calendar_preflight,
        "published_source_commits": [options.source_commit],
        "push_target": "main",
        "resource_budget_id": BUDGET_ID,
        "resource_ceiling_gpu_minutes": 395,
        "resource_class": "one-l40-continuous-latent-temporal",
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
        f"{root}/control-identity.json", f"{root}/streams.json", f"{root}/streams.npz",
        *(f"{root}/seeds/{seed}.json" for seed in SEEDS),
        *(f"{root}/seed-work/{seed}/checkpoint.pt" for seed in SEEDS),
        f"{root}/training.json", *common,
    ]


def plan(options: argparse.Namespace) -> None:
    manifest = verify_assets(options.asset_root, options.source_commit)
    prospective_calendar_preflight(options.asset_root)
    authority_record = json.loads(options.authority.read_text(encoding="utf-8"))
    temporal = json.loads((options.asset_root / "temporal-contract.json").read_text(encoding="utf-8"))
    expected = {(role, candidate, capacity) for role, candidate, capacity in ROLES}
    actual = {(row["role_id"], row["architecture"], row["capacity"]) for row in temporal["roles"]}
    if (
        actual != expected
        or authority_record.get("predecessor_package_evidence")
        != predecessor_bundle()
        or authority_record.get("operational_predecessor_package_evidence")
        != operational_predecessor_bundle(options.source_commit)
    ):
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
            "script": f"job-{role}.sh", "time_limit_minutes": 180,
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
        "admission_materialization": {
            "asset": "materialize_admission.py",
            "receipt_directory": str(
                (options.asset_root / "controller-admissions").resolve()
            ),
            "record_type": "a10m5r12-submission-admission",
            "required_before_each_submit": True,
            "required_roles": [job["role"] for job in jobs],
            "snapshot": "exact private toolkit state plus authenticated job receipts",
            "toolkit_submit_invokes_package_checker": False,
        },
        "operational_predecessor_package_evidence": operational_predecessor_bundle(
            options.source_commit
        ),
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
