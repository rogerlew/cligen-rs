#!/bin/false
"""Publish durable, redacted portable-bootstrap setup diagnostics."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

LOG_LIMIT = 65536
HEX64 = re.compile(r"[0-9a-f]{64}")


def canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def record_hash(value: dict[str, object]) -> str:
    semantic = dict(value)
    semantic.pop("record_sha256", None)
    return hashlib.sha256(canonical(semantic)).hexdigest()


def authenticate_record(value: dict[str, object]) -> bool:
    recorded = value.get("record_sha256")
    return isinstance(recorded, str) and HEX64.fullmatch(recorded) is not None and (
        recorded == record_hash(value)
    )


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {"exists": False}
    return {"bytes": path.stat().st_size, "exists": True, "sha256": digest(path)}


def host_python_identity(path: str) -> dict[str, object]:
    return identity(Path(path))


def tree_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for root, _, files in os.walk(path, followlinks=False):
        for name in files:
            candidate = Path(root) / name
            try:
                total += candidate.lstat().st_size
            except FileNotFoundError:
                continue
    return total


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".promote")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.replace(temporary, path)


def redacted(value: str, run_root: Path, job_local: Path) -> str:
    return value.replace(str(job_local), "[JOB_LOCAL]").replace(
        str(run_root), "[REMOTE_RUN_ROOT]"
    )


def append_log(options: argparse.Namespace) -> None:
    existing = b""
    if options.output.is_file():
        existing = options.output.read_bytes()
    source = b""
    if options.source.is_file():
        source = options.source.read_bytes()
    decoded = source.decode("utf-8", errors="replace")
    section = f"\n[{options.label}]\n{decoded}"
    section = redacted(section, options.run_root, options.job_local).encode("utf-8")
    combined = (existing + section)[-LOG_LIMIT:]
    combined = combined.decode("utf-8", errors="ignore").encode("utf-8")
    options.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = options.output.with_name(options.output.name + ".promote")
    temporary.write_bytes(combined)
    os.replace(temporary, options.output)


def contained(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def record(options: argparse.Namespace) -> None:
    previous: dict[str, object] = {}
    if options.output.is_file():
        previous = json.loads(options.output.read_text(encoding="utf-8"))
    filesystem = os.statvfs(options.job_local)
    current_available = filesystem.f_bavail * filesystem.f_frsize
    current_total = filesystem.f_blocks * filesystem.f_frsize
    prior_storage = previous.get("job_local_storage", {})
    if not isinstance(prior_storage, dict):
        prior_storage = {}
    prior_identities = previous.get("identities", {})
    if not isinstance(prior_identities, dict):
        prior_identities = {}
    asset_paths = {
        "requirements_lock": options.requirements,
        "runtime_archive": options.runtime_archive,
        "wheelhouse_archive": options.wheel_archive,
    }
    measured_identities: dict[str, dict[str, object]] = {}
    for name, path in asset_paths.items():
        measured = prior_identities.get(name)
        if not isinstance(measured, dict) or measured.get("exists") is not True:
            measured = identity(path)
        measured_identities[name] = measured
    manifest = json.loads(options.asset_manifest.read_text(encoding="utf-8"))
    admission = json.loads(options.admission_receipt.read_text(encoding="utf-8"))
    manifest_identity = identity(options.asset_manifest)
    admission_identity = identity(options.admission_receipt)
    expected_identities = {
        name: {
            "bytes": manifest.get("assets", {}).get(path.name, {}).get("bytes"),
            "sha256": manifest.get("assets", {}).get(path.name, {}).get("sha256"),
        }
        for name, path in asset_paths.items()
    }
    actual_identities = {
        name: {"bytes": value.get("bytes"), "sha256": value.get("sha256")}
        for name, value in measured_identities.items()
    }
    asset_identities_authenticated = actual_identities == expected_identities
    source_commit = manifest.get("source_commit")
    admission_authenticated = (
        isinstance(admission, dict)
        and authenticate_record(admission)
        and admission.get("record_type") == "a10m5r10r1r3-submission-admission"
        and admission.get("decision") == "PASS"
        and admission.get("valid") is True
        and admission.get("run_id") == options.run_id
        and admission.get("role") == options.role
        and admission.get("source_commit") == source_commit
        and admission.get("asset_manifest_sha256")
        == manifest_identity.get("sha256")
        and isinstance(admission.get("gates"), dict)
        and bool(admission["gates"])
        and all(value is True for value in admission["gates"].values())
    )
    environment_bytes = tree_bytes(options.job_local / "runtime/environment")
    wheelhouse_bytes = tree_bytes(options.job_local / "wheels")
    paths = {
        "TMPDIR": options.job_local / "tmp",
        "PIP_CACHE_DIR": options.job_local / "pip-cache",
        "XDG_CACHE_HOME": options.job_local / "cache",
        "TORCH_HOME": options.job_local / "torch-cache",
    }
    containment = {
        name: {
            "contained": contained(path, options.job_local),
            "path": redacted(str(path), options.run_root, options.job_local),
        }
        for name, path in paths.items()
    }
    cleanup = {
        "pip_cache_deleted_before_science": not (options.job_local / "pip-cache").exists(),
        "wheelhouse_deleted_before_science": not (options.job_local / "wheels").exists(),
    }
    exit_codes = {
        "host_python_version": options.host_python_version_exit,
        "pip_check": options.pip_check_exit,
        "pip_install": options.pip_install_exit,
        "runtime_version": options.runtime_version_exit,
    }
    ready = bool(options.ready_for_science)
    recorded_python_path = redacted(
        str(Path(options.host_python_path)), options.run_root, options.job_local
    )
    execution_identity = {
        "asset_manifest_sha256": manifest_identity.get("sha256"),
        "host_python_path": recorded_python_path,
        "host_python_version": options.host_python_version,
        "job_id": options.job_id,
        "node": options.node,
        "owner_marker_sha256": options.owner_marker_sha256,
        "role": options.role,
        "run_id": options.run_id,
        "source_commit": source_commit,
        "submission_admission_authenticated": admission_authenticated,
        "submission_admission_record_sha256": admission.get("record_sha256"),
    }
    execution_identity_authenticated = (
        options.run_id
        == "a10m5r10r1r3-corpus-extraction-root-remedy-r0"
        and bool(options.role)
        and options.job_id.isdigit()
        and bool(options.node)
        and HEX64.fullmatch(options.owner_marker_sha256) is not None
        and isinstance(source_commit, str)
        and HEX64.fullmatch(str(manifest_identity.get("sha256"))) is not None
        and Path(options.host_python_path).resolve()
        == (options.job_local / "runtime/cpython/bin/python3").resolve()
        and recorded_python_path == "[JOB_LOCAL]/runtime/cpython/bin/python3"
        and re.fullmatch(r"Python 3\.11\.\d+", options.host_python_version) is not None
        and options.host_python_version_exit == 0
    )
    measured_host_python = host_python_identity(options.host_python_path)
    portable_compute_python_authenticated = (
        measured_host_python.get("exists") is True
        and isinstance(measured_host_python.get("bytes"), int)
        and measured_host_python["bytes"] > 0
        and isinstance(measured_host_python.get("sha256"), str)
        and HEX64.fullmatch(str(measured_host_python["sha256"])) is not None
    )
    valid = (
        ready
        and exit_codes
        == {
            "host_python_version": 0,
            "pip_check": 0,
            "pip_install": 0,
            "runtime_version": 0,
        }
        and all(item["contained"] for item in containment.values())
        and all(cleanup.values())
        and asset_identities_authenticated
        and execution_identity_authenticated
        and portable_compute_python_authenticated
        and admission_authenticated
    )
    first_available = prior_storage.get("available_bytes_before_setup", current_available)
    first_total = prior_storage.get("filesystem_total_bytes", current_total)
    maximum_environment = max(
        int(prior_storage.get("maximum_environment_bytes", 0)), environment_bytes
    )
    maximum_wheelhouse = max(
        int(prior_storage.get("maximum_wheelhouse_bytes", 0)), wheelhouse_bytes
    )
    value = {
        "authentication": {
            "asset_identities_authenticated": asset_identities_authenticated,
            "execution_identity_authenticated": execution_identity_authenticated,
            "portable_compute_python_authenticated": portable_compute_python_authenticated,
            "submission_admission_authenticated": admission_authenticated,
        },
        "cleanup": cleanup,
        "containment": containment,
        "execution_identity": execution_identity,
        "exit_codes": exit_codes,
        "identities": {
            **measured_identities,
            "asset_manifest": manifest_identity,
            "host_python": measured_host_python,
            "submission_admission": admission_identity,
        },
        "job_local_storage": {
            "available_bytes_before_setup": first_available,
            "available_bytes_current": current_available,
            "filesystem_total_bytes": first_total,
            "maximum_environment_bytes": maximum_environment,
            "maximum_wheelhouse_bytes": maximum_wheelhouse,
        },
        "ready_for_science": ready,
        "schema_version": 1,
        "stage": options.stage,
        "valid": valid,
    }
    value["record_sha256"] = record_hash(value)
    atomic_json(options.output, value)


def main() -> None:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    log = commands.add_parser("log")
    log.add_argument("--output", type=Path, required=True)
    log.add_argument("--source", type=Path, required=True)
    log.add_argument("--label", required=True)
    log.add_argument("--run-root", type=Path, required=True)
    log.add_argument("--job-local", type=Path, required=True)
    report = commands.add_parser("record")
    report.add_argument("--output", type=Path, required=True)
    report.add_argument("--stage", required=True)
    report.add_argument("--run-root", type=Path, required=True)
    report.add_argument("--job-local", type=Path, required=True)
    report.add_argument("--wheel-archive", type=Path, required=True)
    report.add_argument("--runtime-archive", type=Path, required=True)
    report.add_argument("--requirements", type=Path, required=True)
    report.add_argument("--asset-manifest", type=Path, required=True)
    report.add_argument("--admission-receipt", type=Path, required=True)
    report.add_argument("--run-id", required=True)
    report.add_argument("--role", required=True)
    report.add_argument("--job-id", required=True)
    report.add_argument("--node", required=True)
    report.add_argument("--owner-marker-sha256", required=True)
    report.add_argument("--host-python-path", required=True)
    report.add_argument("--host-python-version", required=True)
    report.add_argument("--host-python-version-exit", type=int, required=True)
    report.add_argument("--runtime-version-exit", type=int, required=True)
    report.add_argument("--pip-install-exit", type=int, required=True)
    report.add_argument("--pip-check-exit", type=int, required=True)
    report.add_argument("--ready-for-science", action="store_true")
    options = parser.parse_args()
    (append_log if options.command == "log" else record)(options)


if __name__ == "__main__":
    main()
