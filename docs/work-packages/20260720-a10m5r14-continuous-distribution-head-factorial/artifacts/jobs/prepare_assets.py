#!/usr/bin/env python3
"""Prepare R14 from the authenticated executed R13R1 asset tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

PARENT_MANIFEST_SHA256 = "eddd17045a8347ac2b9c919ecba0ce30ca49dbe47e236664e45969fea76f09c9"
PARENT_PACKAGE = "20260720-a10m5r13r1-admission-controller-materialization-remedy"
PARENT_SOURCE_COMMIT = "927c6147f879ed3a9a56ff1218ffaa3953bef93c"
PACKAGE_ID = "20260720-a10m5r14-continuous-distribution-head-factorial"
RUN_ID = "a10m5r14-continuous-distribution-head-factorial-r0"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def verify_parent_assets(
    root: Path, *, expected_manifest_sha256: str = PARENT_MANIFEST_SHA256
) -> dict:
    manifest_path = root / "asset-manifest.json"
    if (
        not manifest_path.is_file() or manifest_path.is_symlink()
        or digest(manifest_path) != expected_manifest_sha256
    ):
        raise RuntimeError("exact executed R13R1 parent manifest identity drift")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("package_id") != PARENT_PACKAGE
        or manifest.get("source_commit") != PARENT_SOURCE_COMMIT
        or manifest.get("protected_roles_opened") != []
        or not isinstance(manifest.get("assets"), dict)
    ):
        raise RuntimeError("R13R1 parent asset authority drift")
    actual = {
        path.name for path in root.iterdir()
        if path.is_file() and path.name != "asset-manifest.json"
    }
    if actual != set(manifest["assets"]):
        raise RuntimeError("R13 parent asset roster drift")
    if {path.name for path in root.iterdir() if path.is_dir()} - {
        "controller-admissions", "__pycache__",
    }:
        raise RuntimeError("unexpected R13 parent asset directory")
    for name, expected in manifest["assets"].items():
        path = root / name
        if path.is_symlink() or path.stat().st_nlink != 1:
            raise RuntimeError(f"unsafe R13R1 parent asset: {name}")
        if identity(path) != {key: expected[key] for key in ("bytes", "sha256")}:
            raise RuntimeError(f"R13R1 parent asset byte drift: {name}")
    return manifest


def git_bytes(repo: Path, commit: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{relative}"), cwd=repo,
        check=True, capture_output=True,
    ).stdout


def committed_write(repo: Path, commit: str, relative: str, target: Path) -> None:
    target.write_bytes(git_bytes(repo, commit, relative))


def prepare(
    parent_root: Path, package: Path, source_commit: str, output: Path,
    *, require_published: bool,
    expected_parent_manifest_sha256: str = PARENT_MANIFEST_SHA256,
) -> dict:
    repo = package.parents[2]
    if require_published:
        head = subprocess.run(
            ("git", "rev-parse", "HEAD"), cwd=repo, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        upstream = subprocess.run(
            ("git", "rev-parse", "origin/main"), cwd=repo, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        branch = subprocess.run(
            ("git", "branch", "--show-current"), cwd=repo, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        if source_commit != head or head != upstream or branch != "main":
            raise RuntimeError("R14 assets require exact published main")
    if output.exists():
        raise RuntimeError("fresh R14 asset output required")
    parent_manifest = verify_parent_assets(
        parent_root, expected_manifest_sha256=expected_parent_manifest_sha256
    )
    shutil.copytree(parent_root, output, symlinks=False)
    shutil.rmtree(output / "__pycache__", ignore_errors=True)
    admissions = output / "controller-admissions"
    if admissions.exists():
        if admissions.is_symlink():
            raise RuntimeError("copied controller admissions are a symlink")
        shutil.rmtree(admissions)
    admissions.mkdir(mode=0o700)
    if any(admissions.iterdir()):
        raise RuntimeError("R14 controller admissions are not fresh")

    source_paths = {
        name: value.get("source_path")
        for name, value in parent_manifest["assets"].items()
        if isinstance(value.get("source_path"), str)
    }
    jobs = package / "artifacts/jobs"
    overlays = {
        "aligned_objective.py": jobs / "aligned_objective.py",
        "build_control_records.py": jobs / "build_control_records.py",
        "climate_core.py": jobs / "climate_core.py",
        "continuous_core.py": jobs / "continuous_core.py",
        "materialize_admission.py": jobs / "materialize_admission.py",
        "objective-selector-coverage.json": package / "artifacts/objective-selector-coverage.json",
        "job-local-capacity-contract.json": package / "artifacts/job-local-capacity-contract.json",
        "portfolio-contract.json": package / "artifacts/portfolio-contract.json",
        "temporal-contract.json": package / "artifacts/temporal-contract.json",
    }
    for role in (
        "continuous-location-ou-k2",
        "continuous-location-ou-smooth-climatology-k2",
        "continuous-location-scale-ou-k2",
        "continuous-location-scale-ou-smooth-climatology-k2",
    ):
        overlays[f"job-{role}.sh"] = jobs / f"job-{role}.sh"
    for name, source in overlays.items():
        relative = source.relative_to(repo).as_posix()
        if require_published:
            committed_write(repo, source_commit, relative, output / name)
        else:
            (output / name).write_bytes(source.read_bytes())
        source_paths[name] = relative

    replacements = {
        "20260720-a10m5r13r1-admission-controller-materialization-remedy": PACKAGE_ID,
        "a10m5r13r1-admission-controller-materialization-remedy-r0": RUN_ID,
        "a10m5r13r1-submission-admission": "a10m5r14-submission-admission",
        "A10M5R13-TEMPORAL-READY": "A10M5R14-TEMPORAL-READY",
        "HOLD-A10M5R13-NO-TEMPORALLY-ELIGIBLE-CANDIDATE": "HOLD-A10M5R14-NO-TEMPORALLY-ELIGIBLE-CANDIDATE",
    }
    operational = (
        "admission_checker.py", "setup_diagnostics.py",
        "job-control-materialization.sh", "job-common-candidate.sh",
        "run_temporal_candidate.sh", "run_control.sh", "temporal_select.py",
        "continuous_candidate_experiment.py",
    )
    for name in operational:
        path = output / name
        text = path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
        source_paths.pop(name, None)

    for name in (
        "job-continuous-hierarchical-latent-process-k2.sh",
        "job-continuous-medium-latent-process-k2.sh",
        "job-selector-aligned-continuous-hierarchy-k2.sh",
        "job-selector-aligned-shared-slow-climate-state-k2.sh",
        "selector_loss.py",
    ):
        (output / name).unlink(missing_ok=True)
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
        "canonical_configuration_id": parent_manifest["canonical_configuration_id"],
        "canonical_configuration_semantic_sha256": parent_manifest["canonical_configuration_semantic_sha256"],
        "package_id": PACKAGE_ID,
        "parent_asset_manifest_sha256": PARENT_MANIFEST_SHA256,
        "protected_roles_opened": [],
        "schema_version": 1,
        "source_commit": source_commit,
    }
    (output / "asset-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-assets", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if re.fullmatch(r"[0-9a-f]{40}", args.source_commit) is None:
        raise RuntimeError("full source commit required")
    prepare(
        args.parent_assets, args.package, args.source_commit, args.output,
        require_published=True,
    )


if __name__ == "__main__":
    main()
