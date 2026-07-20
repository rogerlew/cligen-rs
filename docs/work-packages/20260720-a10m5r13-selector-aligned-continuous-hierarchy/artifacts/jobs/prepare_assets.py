#!/usr/bin/env python3
"""Overlay R13 assets onto an authenticated prepared R12R1 asset directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

EXPECTED = {
    "continuous_core.py": "e1a65062ba0619a1a013fc1e2ea25dd66dcf083f0b71dfbe48ce2e758faa9ed2",
    "continuous_candidate_experiment.py": "b74d0067b2cf9fa792d219c4c36e1cada0b1cda227acaa8a67ac0ffd9f2fc314",
    "temporal_metrics.py": "948d917b910049cb484cd527eace8a079598189f78611cdb4dc64deb82d0663c",
    "temporal_select.py": "49f25fdd453143a1a94eefed2cdf7aaede88f54e75894469eb9395e280f059e7",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def verify_parent_assets(root: Path) -> dict:
    manifest_path = root / "asset-manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        raise RuntimeError("authenticated parent asset manifest absent")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("package_id")
        != "20260719-a10m5r12r1-admission-materialization-remedy"
        or manifest.get("source_commit")
        != "87d38996e1f46ddb47b80c16c9625c16beaede9b"
        or manifest.get("protected_roles_opened") != []
        or not isinstance(manifest.get("assets"), dict)
    ):
        raise RuntimeError("parent manifest authority/provenance drift")
    actual = {
        path.name
        for path in root.iterdir()
        if path.is_file() and path.name != "asset-manifest.json"
    }
    if actual != set(manifest["assets"]):
        raise RuntimeError("parent manifest/file roster drift")
    extra_directories = {
        path.name for path in root.iterdir() if path.is_dir()
    } - {"controller-admissions"}
    if extra_directories:
        raise RuntimeError("unexpected parent asset directory")
    for name, expected in manifest["assets"].items():
        path = root / name
        if path.is_symlink() or path.stat().st_nlink != 1:
            raise RuntimeError(f"unsafe parent asset: {name}")
        if identity(path) != {key: expected[key] for key in ("bytes", "sha256")}:
            raise RuntimeError(f"parent manifest identity drift: {name}")
    for name, expected in EXPECTED.items():
        if digest(root / name) != expected:
            raise RuntimeError(f"prepared parent asset drift: {name}")
    return manifest


def git_bytes(repo: Path, commit: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{relative}"), cwd=repo, check=True,
        capture_output=True,
    ).stdout


def committed_write(repo: Path, commit: str, relative: str, target: Path) -> None:
    target.write_bytes(git_bytes(repo, commit, relative))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-assets", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if re.fullmatch(r"[0-9a-f]{40}", args.source_commit) is None:
        raise RuntimeError("full source commit required")
    repo = args.package.parents[2]
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
    if args.source_commit != head or head != upstream or branch != "main":
        raise RuntimeError("R13 assets require exact published main")
    if args.output.exists():
        raise RuntimeError("fresh R13 asset output required")
    parent_manifest = verify_parent_assets(args.parent_assets)
    shutil.copytree(args.parent_assets, args.output, symlinks=False)
    admission_root = args.output / "controller-admissions"
    if admission_root.exists():
        if admission_root.is_symlink():
            raise RuntimeError("copied controller admission root is a symlink")
        shutil.rmtree(admission_root)
    admission_root.mkdir(mode=0o700)
    jobs = args.package / "artifacts" / "jobs"
    shutil.copy2(args.parent_assets / "continuous_core.py", args.output / "inherited_continuous_core.py")
    source_paths: dict[str, str] = {}
    for name in ("continuous_core.py", "climate_core.py", "selector_loss.py", "build_control_records.py"):
        relative = (jobs / name).relative_to(repo).as_posix()
        committed_write(repo, args.source_commit, relative, args.output / name)
        source_paths[name] = relative
    parent_builder = args.package.parent / "20260719-a10m5r12r1-admission-materialization-remedy" / "artifacts" / "jobs" / "build_control_records.py"
    parent_builder_relative = parent_builder.relative_to(repo).as_posix()
    committed_write(repo, args.source_commit, parent_builder_relative, args.output / "inherited_build_control_records.py")
    source_paths["inherited_build_control_records.py"] = parent_builder_relative
    for name in (
        "job-selector-aligned-continuous-hierarchy-k2.sh",
        "job-selector-aligned-shared-slow-climate-state-k2.sh",
    ):
        relative = (jobs / name).relative_to(repo).as_posix()
        committed_write(repo, args.source_commit, relative, args.output / name)
        source_paths[name] = relative
    for name in (
        "portfolio-contract.json", "temporal-contract.json",
        "job-local-capacity-contract.json",
    ):
        relative = (args.package / "artifacts" / name).relative_to(repo).as_posix()
        committed_write(repo, args.source_commit, relative, args.output / name)
        source_paths[name] = relative
    # The wrapper imports the original R8 implementation under a new name.
    source = args.package.parent / "20260719-a10m5r8-climate-statistics-objective" / "artifacts" / "jobs" / "climate_core.py"
    source_relative = source.relative_to(repo).as_posix()
    source_payload = git_bytes(repo, args.source_commit, source_relative)
    if hashlib.sha256(source_payload).hexdigest() != "50f8863803305ba5012a8de370b9b3aab52d6e536bc730290d18d63f6614b6dd":
        raise RuntimeError("inherited climate core drift")
    (args.output / "inherited_climate_core.py").write_bytes(source_payload)
    source_paths["inherited_climate_core.py"] = source_relative
    replacements = {
        "20260719-a10m5r12r1-admission-materialization-remedy": "20260720-a10m5r13-selector-aligned-continuous-hierarchy",
        "a10m5r12r1-admission-materialization-remedy-r0": "a10m5r13-selector-aligned-continuous-hierarchy-r0",
        "a10m5r12-submission-admission": "a10m5r13-submission-admission",
        "continuous-medium-latent-process-k2": "selector-aligned-continuous-hierarchy-k2",
        "continuous-hierarchical-latent-process-k2": "selector-aligned-shared-slow-climate-state-k2",
        "continuous_medium_latent_process": "selector_aligned_continuous_hierarchy",
        "continuous_hierarchical_latent_process": "selector_aligned_shared_slow_climate_state",
        "A10M5R12-TEMPORAL-READY": "A10M5R13-TEMPORAL-READY",
        "HOLD-A10M5R12-NO-TEMPORALLY-ELIGIBLE-CANDIDATE": "HOLD-A10M5R13-NO-TEMPORALLY-ELIGIBLE-CANDIDATE",
    }
    operational = (
        "admission_checker.py", "materialize_admission.py", "setup_diagnostics.py",
        "job-control-materialization.sh", "job-common-candidate.sh",
        "run_temporal_candidate.sh", "run_control.sh", "temporal_select.py",
        "continuous_candidate_experiment.py",
    )
    for name in operational:
        path = args.output / name
        text = path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")
    experiment = args.output / "continuous_candidate_experiment.py"
    experiment_text = experiment.read_text(encoding="utf-8")
    needle = '            "physical_support": all(row["candidate"]["support"] for row in seed_rows),\n'
    if experiment_text.count(needle) != 1:
        raise RuntimeError("candidate evidence gate insertion point drift")
    experiment.write_text(
        experiment_text.replace(
            needle,
            '            "science_self_tests": True,\n' + needle,
        ),
        encoding="utf-8",
    )
    for path in args.output.iterdir():
        if path.is_file() and path.suffix in (".py", ".sh"):
            path.chmod(0o700)
    assets = {}
    for path in sorted(args.output.iterdir()):
        if path.is_file() and path.name != "asset-manifest.json":
            assets[path.name] = {
                **identity(path),
                **({"source_path": source_paths[path.name]} if path.name in source_paths else {}),
            }
    manifest = {
        "assets": assets,
        "canonical_configuration_id": parent_manifest["canonical_configuration_id"],
        "canonical_configuration_semantic_sha256": parent_manifest["canonical_configuration_semantic_sha256"],
        "package_id": "20260720-a10m5r13-selector-aligned-continuous-hierarchy",
        "protected_roles_opened": [],
        "schema_version": 1,
        "source_commit": args.source_commit,
    }
    (args.output / "asset-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
