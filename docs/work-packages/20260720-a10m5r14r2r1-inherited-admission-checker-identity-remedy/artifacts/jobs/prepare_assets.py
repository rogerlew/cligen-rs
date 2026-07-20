#!/usr/bin/env python3
"""Prepare R14R2R1 from the exact authenticated R14R2 asset tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

PARENT_MANIFEST_SHA256 = "574af046f382ea992925cb68b162af553e0b712530b8f4a5894bb47a85bef21a"
PARENT_PACKAGE = "20260720-a10m5r14r2-shared-environment-four-l40-portfolio"
PARENT_RUN = "a10m5r14r2-shared-environment-four-l40-portfolio-r0"
PARENT_SOURCE_COMMIT = "3a9f2aedab1f7be5202a141c7d32350d7fe6f5e3"
PACKAGE_ID = "20260720-a10m5r14r2r1-inherited-admission-checker-identity-remedy"
RUN_ID = "a10m5r14r2r1-inherited-admission-checker-identity-remedy-r0"
TOOLKIT_COMMIT = "06df84c882fbe297e93b13fb8c845d5eb500b405"
CHECKER_SLOTS = ["admission_checker.py", "inherited_admission_checker.py"]
OVERLAYS = {
    "admission_checker.py": "artifacts/jobs/admission_checker.py",
    "build_control_records.py": "artifacts/jobs/build_control_records.py",
    "materialize_admission.py": "artifacts/jobs/materialize_admission.py",
    "run_temporal_replay.py": "artifacts/run_temporal_replay.py",
}
OPERATIONAL_REWRITES = {
    "inherited_admission_checker.py",
    "job-control-materialization.sh",
    "job-continuous-distribution-head-factorial-portfolio.sh",
    "job-local-capacity-contract.json",
    "portfolio_launcher.py",
    "setup_diagnostics.py",
    "temporal_select.py",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def git_bytes(repo: Path, commit: str, relative: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{relative}"), cwd=repo, check=True, capture_output=True
    ).stdout


def verify_parent(root: Path) -> dict:
    manifest_path = root / "asset-manifest.json"
    if not manifest_path.is_file() or digest(manifest_path) != PARENT_MANIFEST_SHA256:
        raise RuntimeError("exact R14R2 parent manifest identity drift")
    manifest = json.loads(manifest_path.read_text())
    if not (
        manifest.get("package_id") == PARENT_PACKAGE
        and manifest.get("source_commit") == PARENT_SOURCE_COMMIT
        and manifest.get("protected_roles_opened") == []
        and isinstance(manifest.get("assets"), dict)
    ):
        raise RuntimeError("R14R2 parent asset authority drift")
    actual = {p.name for p in root.iterdir() if p.is_file() and p.name != manifest_path.name}
    if actual != set(manifest["assets"]):
        raise RuntimeError("R14R2 parent asset roster drift")
    unexpected_directories = {
        path.name for path in root.iterdir() if path.is_dir()
    } - {"controller-admissions", "__pycache__"}
    if unexpected_directories:
        raise RuntimeError("unexpected R14R2 parent asset directory")
    for name, expected in manifest["assets"].items():
        path = root / name
        if path.is_symlink() or path.stat().st_nlink != 1:
            raise RuntimeError(f"unsafe R14R2 parent asset: {name}")
        if identity(path) != {key: expected[key] for key in ("bytes", "sha256")}:
            raise RuntimeError(f"R14R2 parent asset byte drift: {name}")
    return manifest


def derive_inherited_checker(path: Path) -> None:
    """Migrate the real inherited checker from hard-coded slot 0 to exact slot 1."""
    text = path.read_text()
    anchor = "    remote_root = options.remote_run_root.resolve()\n"
    addition = anchor + (
        "    try:\n"
        "        self_logical_name = Path(__file__).resolve().relative_to(remote_root).as_posix()\n"
        "    except ValueError as error:\n"
        "        raise RuntimeError('inherited checker escapes exact remote root') from error\n"
        "    checker_contract = plan.get('admission_materialization', {}).get('checker_assets')\n"
        "    checker_names = checker_contract.get('logical_names') if isinstance(checker_contract, dict) else None\n"
    )
    if text.count(anchor) != 1:
        raise RuntimeError("inherited checker remote-root anchor drift")
    text = text.replace(anchor, addition)
    old_gate = (
        '        "staged_admission_checker_plan_identity": (\n'
        '            plan_assets.get("admission_checker.py", {}).get("bytes")\n'
        '            == Path(__file__).stat().st_size\n'
        '            and plan_assets.get("admission_checker.py", {}).get("sha256")\n'
        '            == digest(Path(__file__))\n'
        "        ),\n"
    )
    new_gate = (
        '        "staged_admission_checker_plan_identity": (\n'
        "            isinstance(checker_contract, dict)\n"
        "            and checker_contract.get('protocol') == 'ordered-plan-assets-v1'\n"
        "            and checker_names == ['admission_checker.py', 'inherited_admission_checker.py']\n"
        "            and self_logical_name == checker_names[1]\n"
        "            and not Path(__file__).is_symlink()\n"
        "            and Path(__file__).stat().st_nlink == 1\n"
        "            and plan_assets.get(self_logical_name, {}).get('bytes') == Path(__file__).stat().st_size\n"
        "            and plan_assets.get(self_logical_name, {}).get('sha256') == digest(Path(__file__))\n"
        "            and manifest.get('assets', {}).get(self_logical_name, {}).get('bytes') == Path(__file__).stat().st_size\n"
        "            and manifest.get('assets', {}).get(self_logical_name, {}).get('sha256') == digest(Path(__file__))\n"
        "        ),\n"
    )
    if text.count(old_gate) != 1:
        raise RuntimeError("inherited checker self-identity gate drift")
    path.write_text(text.replace(old_gate, new_gate))


def verify_abort(package: Path) -> dict:
    path = package / "artifacts/parent-pre-submission-abort.json"
    if digest(path) != "7f3c7c6a9e73cb3114310cf7ecf1bcaf5ba82bc9f8cef61710f7598693d33e24":
        raise RuntimeError("R14R2 abort evidence identity drift")
    value = json.loads(path.read_text())
    if not (
        value.get("source_commit") == PARENT_SOURCE_COMMIT
        and value.get("terminal") == "LEMHI-TOOLKIT-RUN-ABORTED-BEFORE-SUBMISSION"
        and value.get("remote_absent") is True
        and value.get("job_local_cleanup") == "not_started"
    ):
        raise RuntimeError("R14R2 abort evidence semantic drift")
    return value


def prepare(parent_root: Path, package: Path, source_commit: str, output: Path, *, require_published: bool) -> dict:
    repo = package.parents[2]
    verify_abort(package)
    parent = verify_parent(parent_root)
    if require_published:
        head = subprocess.run(("git", "rev-parse", "HEAD"), cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
        upstream = subprocess.run(("git", "rev-parse", "origin/main"), cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
        branch = subprocess.run(("git", "branch", "--show-current"), cwd=repo, check=True, capture_output=True, text=True).stdout.strip()
        if source_commit != head or head != upstream or branch != "main":
            raise RuntimeError("R14R2R1 assets require exact published main")
        ancestor = subprocess.run(
            ("git", "merge-base", "--is-ancestor", TOOLKIT_COMMIT, source_commit),
            cwd=repo,
            check=False,
        ).returncode == 0
        toolkit_unchanged = subprocess.run(
            (
                "git", "diff", "--quiet", TOOLKIT_COMMIT, source_commit, "--",
                "research/a10/lemhi_toolkit", "docs/specifications/SPEC-LEMHI-AGENT-TOOLKIT.md",
            ),
            cwd=repo,
            check=False,
        ).returncode == 0
        if not ancestor or not toolkit_unchanged:
            raise RuntimeError("ratified composed-checker toolkit prerequisite drift")
    if output.exists():
        raise RuntimeError("fresh R14R2R1 asset output required")
    shutil.copytree(parent_root, output, symlinks=False)
    shutil.rmtree(output / "__pycache__", ignore_errors=True)
    shutil.rmtree(output / "controller-admissions", ignore_errors=True)
    (output / "controller-admissions").mkdir(mode=0o700)
    source_paths = {
        name: item["source_path"]
        for name, item in parent["assets"].items()
        if isinstance(item.get("source_path"), str)
    }
    for name, relative in OVERLAYS.items():
        source = package / relative
        repo_relative = source.relative_to(repo).as_posix()
        (output / name).write_bytes(
            git_bytes(repo, source_commit, repo_relative) if require_published else source.read_bytes()
        )
        source_paths[name] = repo_relative
    for name in OPERATIONAL_REWRITES:
        path = output / name
        if not path.is_file():
            raise RuntimeError(f"missing inherited operational asset: {name}")
        text = path.read_text().replace(PARENT_PACKAGE, PACKAGE_ID).replace(PARENT_RUN, RUN_ID)
        text = text.replace("a10m5r14r2-submission-admission", "a10m5r14r2r1-submission-admission")
        text = text.replace("a10m5r14r2-immediate-pre-submit-occupancy", "a10m5r14r2r1-immediate-pre-submit-occupancy")
        path.write_text(text)
        source_paths.pop(name, None)
    derive_inherited_checker(output / CHECKER_SLOTS[1])
    for path in output.iterdir():
        if path.is_file() and path.suffix in {".py", ".sh"}:
            path.chmod(0o700)
    parent_names = set(parent["assets"])
    current_names = {
        path.name
        for path in output.iterdir()
        if path.is_file() and path.name != "asset-manifest.json"
    }
    changed = (parent_names ^ current_names) | {
        name
        for name, expected in parent["assets"].items()
        if name in current_names
        if identity(output / name)
        != {key: expected[key] for key in ("bytes", "sha256")}
    }
    expected_changed = set(OVERLAYS) | OPERATIONAL_REWRITES
    if changed != expected_changed:
        raise RuntimeError(
            f"R14R2R1 operational changed-file roster drift: {sorted(changed)}"
        )
    for name in OPERATIONAL_REWRITES:
        text = (output / name).read_text()
        if PARENT_RUN in text or "a10m5r14r2-submission-admission" in text:
            raise RuntimeError(f"stale R14R2 operational identity remains: {name}")
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
        "checker_assets": {"logical_names": CHECKER_SLOTS, "protocol": "ordered-plan-assets-v1"},
        "package_id": PACKAGE_ID,
        "parent_asset_manifest_sha256": PARENT_MANIFEST_SHA256,
        "protected_roles_opened": [],
        "schema_version": 1,
        "source_commit": source_commit,
        "toolkit_prerequisite_commit": TOOLKIT_COMMIT,
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
