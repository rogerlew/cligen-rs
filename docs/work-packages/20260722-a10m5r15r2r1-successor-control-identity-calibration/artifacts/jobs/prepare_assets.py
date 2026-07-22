#!/usr/bin/env python3
"""Prepare candidate-blind successor control-calibration assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PACKAGE_ID = "20260722-a10m5r15r2r1-successor-control-identity-calibration"
RUN_ID = "a10m5r15r2r1-successor-control-identity-calibration-r1"
RECORD_TYPE = "a10m5r15r2r1-submission-admission"
PARENT_PACKAGE_ID = "20260721-a10m5r15r2-external-normal-conditioning-execution"
PARENT_RUN_ID = "a10m5r15r2-external-normal-conditioning-execution-r0"
PARENT_RECORD_TYPE = "a10m5r15r2-submission-admission"
PARENT_MANIFEST_SHA256 = (
    "64a5595fab4b493c5985db3e0a271ec6eeaa7d2dcdbe77c10e7f97d5474f988b"
)
PARENT_SOURCE_COMMIT = "b38f695697a8636e67f041ccae373107cb5cb5bc"
CONTROL_ROLE = "control-materialization"
LARGE_IMMUTABLE = {
    "cargo-vendor.tar.gz",
    "corpus.tar",
    "runtime.tar.gz",
    "rust-1.92.0-x86_64-unknown-linux-gnu.tar.xz",
    "wheelhouse.tar",
}


def canonical(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def git_bytes(commit: str, path: Path) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path.relative_to(REPO).as_posix()}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


def copy_parent(parent: Path, output: Path) -> None:
    output.mkdir(mode=0o700)
    for source in parent.iterdir():
        target = output / source.name
        if source.name in {"controller-admissions", "__pycache__"}:
            continue
        if source.is_dir():
            shutil.copytree(source, target)
        elif source.name in LARGE_IMMUTABLE:
            cloned = subprocess.run(
                ("cp", "-c", "-p", str(source), str(target)),
                check=False,
                capture_output=True,
            )
            if cloned.returncode != 0:
                shutil.copy2(source, target)
            if target.stat().st_nlink != 1:
                raise RuntimeError(f"copied asset is not link-isolated: {source.name}")
        else:
            shutil.copy2(source, target)
    (output / "controller-admissions").mkdir(mode=0o700)


def verify_parent_layout(parent_root: Path, manifest: dict) -> None:
    assets = manifest.get("assets")
    if not isinstance(assets, dict) or not assets:
        raise RuntimeError("parent manifest asset map missing")
    entries = {path.name for path in parent_root.iterdir()}
    allowed = set(assets) | {"asset-manifest.json", "controller-admissions"}
    if entries - allowed:
        raise RuntimeError("unexpected parent asset entry")
    directories = {path.name for path in parent_root.iterdir() if path.is_dir()}
    if directories - {"controller-admissions"}:
        raise RuntimeError("unexpected parent asset directory")
    admissions = parent_root / "controller-admissions"
    if admissions.is_symlink() or not admissions.is_dir():
        raise RuntimeError("parent controller-admissions is not a regular directory")
    manifest_path = parent_root / "asset-manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise RuntimeError("parent asset manifest is not a regular file")
    files = {
        path.name
        for path in parent_root.iterdir()
        if path.is_file() and path.name != "asset-manifest.json"
    }
    if files != set(assets):
        raise RuntimeError("parent asset file set differs from manifest")
    for name, expected in assets.items():
        path = parent_root / name
        if (
            path.is_symlink()
            or not path.is_file()
            or identity(path)
            != {key: expected.get(key) for key in ("bytes", "sha256")}
        ):
            raise RuntimeError(f"parent asset identity drift: {name}")


def verify_copied_parent(parent_manifest: dict, output: Path) -> None:
    for name, expected in parent_manifest["assets"].items():
        path = output / name
        if (
            path.is_symlink()
            or not path.is_file()
            or identity(path)
            != {key: expected.get(key) for key in ("bytes", "sha256")}
        ):
            raise RuntimeError(f"copied parent asset identity drift: {name}")


def transform_text_assets(output: Path) -> None:
    replacements = {
        PARENT_PACKAGE_ID: PACKAGE_ID,
        PARENT_RUN_ID: RUN_ID,
        PARENT_RECORD_TYPE: RECORD_TYPE,
    }
    overlays = {
        "build_control_records.py",
        "materialize_admission.py",
        "materialize_controls.py",
    }
    for path in output.iterdir():
        if (
            not path.is_file()
            or path.name in overlays
            or path.suffix not in {".py", ".sh"}
        ):
            continue
        text = path.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")


def rewrite_capacity(output: Path) -> None:
    path = output / "job-local-capacity-contract.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    value["package_id"] = PACKAGE_ID
    # The inherited plan builder authenticates this exact operational status
    # before the successor projects the candidate jobs away.
    value["status"] = "EXECUTION-READY"
    value["admission"]["waves"] = []
    value["resources"].update(
        {
            "allocation_job_count": 0,
            "candidate_process_count": 0,
            "candidate_role_count": 0,
            "control_minutes": 30,
            "gpus_per_portfolio": 0,
            "independent_process_count": 0,
            "portfolio_minutes": 0,
            "process_waves": 0,
            "recovery_minutes": 5,
            "science_arm_count": 0,
            "simultaneous_candidate_processes": 0,
            "total_gpu_minute_ceiling": 35,
        }
    )
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent-assets", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    if re.fullmatch(r"[0-9a-f]{40}", options.source_commit) is None:
        raise RuntimeError("full source commit required")
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    upstream = subprocess.run(
        ("git", "rev-parse", "origin/main"),
        cwd=REPO,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if head != upstream or head != options.source_commit:
        raise RuntimeError("calibration assets require exact published main")
    parent_manifest_path = options.parent_assets / "asset-manifest.json"
    parent = json.loads(parent_manifest_path.read_text(encoding="utf-8"))
    if not (
        digest(parent_manifest_path) == PARENT_MANIFEST_SHA256
        and parent.get("package_id") == PARENT_PACKAGE_ID
        and parent.get("source_commit") == PARENT_SOURCE_COMMIT
        and parent.get("protected_roles_opened") == []
        and parent.get("assets", {}).get("corpus.tar", {}).get("sha256")
        == "7b41e497d215c85ae734dea438424f23ae01cff59a3b3ba55ec32442578553f2"
    ):
        raise RuntimeError("parent execution assets differ from closed R2 run")
    verify_parent_layout(options.parent_assets, parent)
    if options.output.exists():
        raise RuntimeError("fresh calibration asset output required")
    copy_parent(options.parent_assets, options.output)
    verify_copied_parent(parent, options.output)
    transform_text_assets(options.output)
    rewrite_capacity(options.output)
    overlays = {
        "build_control_records.py": PACKAGE
        / "artifacts/jobs/build_control_records.py",
        "materialize_admission.py": PACKAGE
        / "artifacts/jobs/materialize_admission.py",
        "materialize_controls.py": PACKAGE
        / "artifacts/jobs/materialize_controls.py",
        "control-calibration-contract.json": PACKAGE
        / "artifacts/control-calibration-contract.json",
        "control-role-map.json": PACKAGE / "artifacts/control-role-map.json",
    }
    for name, source in overlays.items():
        (options.output / name).write_bytes(git_bytes(options.source_commit, source))
    for path in options.output.iterdir():
        if path.is_file() and path.suffix in {".py", ".sh"}:
            path.chmod(0o700)
    assets = {
        path.name: {
            **identity(path),
            **(
                {"source_path": source.relative_to(REPO).as_posix()}
                if (source := overlays.get(path.name)) is not None
                else {}
            ),
        }
        for path in sorted(options.output.iterdir())
        if path.is_file() and path.name != "asset-manifest.json"
    }
    manifest = {
        "assets": assets,
        "canonical_configuration_id": parent["canonical_configuration_id"],
        "canonical_configuration_semantic_sha256": parent[
            "canonical_configuration_semantic_sha256"
        ],
        "package_id": PACKAGE_ID,
        "parent_asset_manifest_sha256": PARENT_MANIFEST_SHA256,
        "protected_roles_opened": [],
        "schema_version": 1,
        "source_commit": options.source_commit,
    }
    manifest_path = options.output / "asset-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"A10M5R15R2R1-ASSETS-PREPARED {digest(manifest_path)}")


if __name__ == "__main__":
    main()
