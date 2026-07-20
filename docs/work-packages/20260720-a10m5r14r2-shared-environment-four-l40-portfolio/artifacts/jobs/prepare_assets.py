#!/usr/bin/env python3
"""Prepare R14R2 from the exact authenticated R14R1 asset tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

PARENT_MANIFEST_SHA256 = "ba0b61e77d15a014ea7bed507af0bdd1c3724d15e8d9d3413cac80c23ddd994e"
PARENT_PACKAGE = "20260720-a10m5r14r1-admission-role-matrix-remedy"
PARENT_SOURCE_COMMIT = "bbb3075109ce06dabda13d43862cd94d375225bd"
PACKAGE_ID = "20260720-a10m5r14r2-shared-environment-four-l40-portfolio"
RUN_ID = "a10m5r14r2-shared-environment-four-l40-portfolio-r0"
SCIENCE_HASHES = {
    "aligned_objective.py": "8f5185919f3d0189a7cd9d9552349747e99db9dde8047c964c6050e9ac77fff1",
    "climate_core.py": "f9e9eb96b5909034f410f475ae9f1ad89bcb2f4cc0cc26453338bb939ccf31f9",
    "continuous_core.py": "f4a3f256e95dc76cffcd709fcd1d6559adbfcdc0cce231d8e0f23efdab10b798",
    "objective-selector-coverage.json": "8b77b1b50e0e961ef54ff1a71a5206c561a6fa86163473ffd3fbcd9a5b1b3f04",
    "portfolio-contract.json": "d39fe5e1b8e5a82ddd758aedd1e2aacb6acc72509de6b986cdae574c82937a8e",
    "temporal-contract.json": "a3e0456ae991e3e965e64696104d76c6b01c7248e80822d0f13982e622262b35",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def canonical(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode()


def verify_bound_evidence(package: Path, inheritance: dict) -> tuple[dict, Path]:
    contract_path = package / inheritance["predecessor_evidence_contract"]
    contract = json.loads(contract_path.read_text())
    binding = contract.get("execution_bindings", {})
    path = package.parents[2] / binding.get("path", "")
    if (
        contract.get("schema_version") != 1
        or not path.is_file()
        or path.is_symlink()
        or digest(path) != binding.get("sha256")
    ):
        raise RuntimeError("R14R1 execution bindings identity drift")
    actual = json.loads(path.read_text())
    expected = dict(contract)
    expected.pop("execution_bindings")
    expected.pop("schema_version")
    if actual != expected:
        raise RuntimeError("R14R1 nested execution evidence identity drift")
    if (
        actual.get("source_commit") != PARENT_SOURCE_COMMIT
        or actual.get("run_id") != "a10m5r14r1-admission-role-matrix-remedy-r0"
        or actual.get("terminal", {}).get("terminal") != "LEMHI-TOOLKIT-RUN-CLOSED"
        or actual.get("terminal", {}).get("remote_absent") is not True
        or actual.get("terminal", {}).get("job_local_cleanup") != "verified_absent"
        or actual.get("actual_gpu_minutes") != 88
    ):
        raise RuntimeError("R14R1 execution bindings semantic drift")
    return actual, path


def git_bytes(repo: Path, commit: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{relative}"), cwd=repo, check=True, capture_output=True
    ).stdout


def verify_predecessor(package: Path) -> dict:
    inheritance = json.loads((package / "artifacts/inheritance-manifest.json").read_text())
    value, _ = verify_bound_evidence(package, inheritance)
    return value


def verify_parent_assets(root: Path) -> dict:
    manifest_path = root / "asset-manifest.json"
    if not manifest_path.is_file() or digest(manifest_path) != PARENT_MANIFEST_SHA256:
        raise RuntimeError("exact R14R1 parent manifest identity drift")
    manifest = json.loads(manifest_path.read_text())
    if (
        manifest.get("package_id") != PARENT_PACKAGE
        or manifest.get("source_commit") != PARENT_SOURCE_COMMIT
        or manifest.get("protected_roles_opened") != []
        or not isinstance(manifest.get("assets"), dict)
    ):
        raise RuntimeError("R14R1 parent asset authority drift")
    actual = {path.name for path in root.iterdir() if path.is_file() and path.name != "asset-manifest.json"}
    if actual != set(manifest["assets"]):
        raise RuntimeError("R14R1 parent asset roster drift")
    if {path.name for path in root.iterdir() if path.is_dir()} - {"controller-admissions", "__pycache__"}:
        raise RuntimeError("unexpected R14R1 parent asset directory")
    for name, expected in manifest["assets"].items():
        path = root / name
        if path.is_symlink() or path.stat().st_nlink != 1:
            raise RuntimeError(f"unsafe R14R1 parent asset: {name}")
        if identity(path) != {key: expected[key] for key in ("bytes", "sha256")}:
            raise RuntimeError(f"R14R1 parent asset byte drift: {name}")
    for name, expected in SCIENCE_HASHES.items():
        if digest(root / name) != expected:
            raise RuntimeError(f"frozen R14 science drift: {name}")
    return manifest


def prepare(parent_root: Path, package: Path, source_commit: str, output: Path, *, require_published: bool) -> dict:
    repo = package.parents[2]
    verify_predecessor(package)
    parent = verify_parent_assets(parent_root)
    if require_published:
        head = subprocess.run(("git", "rev-parse", "HEAD"), cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
        upstream = subprocess.run(("git", "rev-parse", "origin/main"), cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
        branch = subprocess.run(("git", "branch", "--show-current"), cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
        if source_commit != head or head != upstream or branch != "main":
            raise RuntimeError("R14R2 assets require exact published main")
    if output.exists():
        raise RuntimeError("fresh R14R2 asset output required")
    shutil.copytree(parent_root, output, symlinks=False)
    shutil.rmtree(output / "__pycache__", ignore_errors=True)
    shutil.rmtree(output / "controller-admissions", ignore_errors=True)
    (output / "controller-admissions").mkdir(mode=0o700)
    (output / "admission_checker.py").replace(output / "inherited_admission_checker.py")
    (output / "continuous_core.py").replace(output / "inherited_r14_continuous_core.py")
    for obsolete in (
        "job-continuous-location-ou-k2.sh",
        "job-continuous-location-ou-smooth-climatology-k2.sh",
        "job-continuous-location-scale-ou-k2.sh",
        "job-continuous-location-scale-ou-smooth-climatology-k2.sh",
        "job-common-candidate.sh",
        "run_temporal_candidate.sh",
    ):
        (output / obsolete).unlink()

    overlays = {
        "admission_checker.py": package / "artifacts/jobs/admission_checker.py",
        "build_control_records.py": package / "artifacts/jobs/build_control_records.py",
        "job-local-capacity-contract.json": package / "artifacts/job-local-capacity-contract.json",
        "device-binding-qualification.json": package / "artifacts/device-binding-qualification.json",
        "continuous_core.py": package / "artifacts/jobs/continuous_core.py",
        "portfolio-role-map.json": package / "artifacts/portfolio-role-map.json",
        "portfolio_candidate_process.py": package / "artifacts/jobs/portfolio_candidate_process.py",
        "portfolio_launcher.py": package / "artifacts/jobs/portfolio_launcher.py",
        "parameter_accounting.py": package / "artifacts/jobs/parameter_accounting.py",
        "materialize_admission.py": package / "artifacts/jobs/materialize_admission.py",
        "run_portfolio.sh": package / "artifacts/jobs/run_portfolio.sh",
        "job-continuous-distribution-head-factorial-portfolio.sh": package
        / "artifacts/jobs/job-continuous-distribution-head-factorial-portfolio.sh",
    }
    source_paths = {
        name: value.get("source_path")
        for name, value in parent["assets"].items()
        if isinstance(value.get("source_path"), str)
    }
    for name, source in overlays.items():
        relative = source.relative_to(repo).as_posix()
        (output / name).write_bytes(
            git_bytes(repo, source_commit, relative) if require_published else source.read_bytes()
        )
        source_paths[name] = relative

    for name in (
        "inherited_admission_checker.py",
        "setup_diagnostics.py",
        "job-control-materialization.sh",
        "run_control.sh",
        "temporal_select.py",
    ):
        path = output / name
        text = path.read_text().replace(PARENT_PACKAGE, PACKAGE_ID)
        text = text.replace("a10m5r14r1-admission-role-matrix-remedy-r0", RUN_ID)
        text = text.replace("a10m5r14r1-submission-admission", "a10m5r14r2-submission-admission")
        path.write_text(text)
        source_paths.pop(name, None)

    for path in output.iterdir():
        if path.is_file() and path.suffix in (".py", ".sh"):
            path.chmod(0o700)
    assets = {}
    for path in sorted(output.iterdir()):
        if path.is_file() and path.name != "asset-manifest.json":
            assets[path.name] = {
                **identity(path),
                **({"source_path": source_paths[path.name]} if path.name in source_paths else {}),
            }
    manifest = {
        "assets": assets,
        "canonical_configuration_id": parent["canonical_configuration_id"],
        "canonical_configuration_semantic_sha256": parent["canonical_configuration_semantic_sha256"],
        "package_id": PACKAGE_ID,
        "parent_asset_manifest_sha256": PARENT_MANIFEST_SHA256,
        "protected_roles_opened": [],
        "schema_version": 1,
        "source_commit": source_commit,
    }
    (output / "asset-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-assets", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    if re.fullmatch(r"[0-9a-f]{40}", options.source_commit) is None:
        raise RuntimeError("full source commit required")
    prepare(options.parent_assets, options.package, options.source_commit, options.output, require_published=True)


if __name__ == "__main__":
    main()
