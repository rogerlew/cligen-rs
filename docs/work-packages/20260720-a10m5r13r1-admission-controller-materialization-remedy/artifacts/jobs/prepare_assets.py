#!/usr/bin/env python3
"""Prepare R13R1 from the authenticated real R13 asset tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

PARENT_MANIFEST_SHA256 = "d9c526e8989516e71a4840fe42d09f86c048f80835f83157b97a72ea47aa84f8"
PARENT_PACKAGE = "20260720-a10m5r13-selector-aligned-continuous-hierarchy"
PARENT_SOURCE_COMMIT = "6ded2b6b43d6c87efc43776e9b1f730217736574"
PACKAGE_ID = "20260720-a10m5r13r1-admission-controller-materialization-remedy"
RUN_ID = "a10m5r13r1-admission-controller-materialization-remedy-r0"


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
        raise RuntimeError("exact R13 parent manifest identity drift")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("package_id") != PARENT_PACKAGE
        or manifest.get("source_commit") != PARENT_SOURCE_COMMIT
        or manifest.get("protected_roles_opened") != []
        or not isinstance(manifest.get("assets"), dict)
    ):
        raise RuntimeError("R13 parent asset authority drift")
    actual = {
        path.name for path in root.iterdir()
        if path.is_file() and path.name != "asset-manifest.json"
    }
    if actual != set(manifest["assets"]):
        raise RuntimeError("R13 parent asset roster drift")
    if {path.name for path in root.iterdir() if path.is_dir()} - {"controller-admissions"}:
        raise RuntimeError("unexpected R13 parent asset directory")
    for name, expected in manifest["assets"].items():
        path = root / name
        if path.is_symlink() or path.stat().st_nlink != 1:
            raise RuntimeError(f"unsafe R13 parent asset: {name}")
        if identity(path) != {key: expected[key] for key in ("bytes", "sha256")}:
            raise RuntimeError(f"R13 parent asset byte drift: {name}")
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
            raise RuntimeError("R13R1 assets require exact published main")
    if output.exists():
        raise RuntimeError("fresh R13R1 asset output required")
    parent_manifest = verify_parent_assets(
        parent_root, expected_manifest_sha256=expected_parent_manifest_sha256
    )
    shutil.copytree(parent_root, output, symlinks=False)
    admissions = output / "controller-admissions"
    if admissions.exists():
        if admissions.is_symlink():
            raise RuntimeError("copied controller admissions are a symlink")
        shutil.rmtree(admissions)
    admissions.mkdir(mode=0o700)
    if any(admissions.iterdir()):
        raise RuntimeError("R13R1 controller admissions are not fresh")

    source_paths = {
        name: value.get("source_path")
        for name, value in parent_manifest["assets"].items()
        if isinstance(value.get("source_path"), str)
    }
    jobs = package / "artifacts/jobs"
    overlays = {
        "build_control_records.py": jobs / "build_control_records.py",
        "materialize_admission.py": jobs / "materialize_admission.py",
        "job-local-capacity-contract.json": package / "artifacts/job-local-capacity-contract.json",
    }
    for name, source in overlays.items():
        relative = source.relative_to(repo).as_posix()
        if require_published:
            committed_write(repo, source_commit, relative, output / name)
        else:
            (output / name).write_bytes(source.read_bytes())
        source_paths[name] = relative

    replacements = {
        "20260720-a10m5r13-selector-aligned-continuous-hierarchy": PACKAGE_ID,
        "a10m5r13-selector-aligned-continuous-hierarchy-r0": RUN_ID,
        "a10m5r13-submission-admission": "a10m5r13r1-submission-admission",
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
