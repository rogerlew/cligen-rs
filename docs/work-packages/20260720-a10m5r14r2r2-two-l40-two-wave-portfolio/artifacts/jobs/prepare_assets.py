#!/usr/bin/env python3
"""Prepare the R14R2R2 two-L40 successor from exact R14R2R1 assets."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

PARENT_COMMIT = "6463ab2bebcf016c371afc56e31ffc7156a2fb95"
PARENT_PACKAGE_ID = "20260720-a10m5r14r2r1-inherited-admission-checker-identity-remedy"
PARENT_RUN_ID = "a10m5r14r2r1-inherited-admission-checker-identity-remedy-r0"
PACKAGE_ID = "20260720-a10m5r14r2r2-two-l40-two-wave-portfolio"
RUN_ID = "a10m5r14r2r2-two-l40-two-wave-portfolio-r0"
PARENT_RECORD = "a10m5r14r2r1-submission-admission"
RECORD = "a10m5r14r2r2-submission-admission"
TOOLKIT_COMMIT = "06df84c882fbe297e93b13fb8c845d5eb500b405"
IDENTITY_REWRITES = {
    "admission_checker.py",
    "inherited_admission_checker.py",
    "job-continuous-distribution-head-factorial-portfolio.sh",
    "job-control-materialization.sh",
    "portfolio_launcher.py",
    "run_temporal_replay.py",
    "setup_diagnostics.py",
    "temporal_select.py",
}
OVERLAYS = {
    "build_control_records.py": "artifacts/jobs/build_control_records.py",
    "job-local-capacity-contract.json": "artifacts/job-local-capacity-contract.json",
    "materialize_admission.py": "artifacts/jobs/materialize_admission.py",
    "portfolio-role-map.json": "artifacts/portfolio-role-map.json",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"bytes": path.stat().st_size, "sha256": digest(path)}


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"{label} anchor drift")
    return text.replace(old, new)


def load_parent(repo: Path):
    source = repo / "docs/work-packages" / PARENT_PACKAGE_ID / "artifacts/jobs/prepare_assets.py"
    published = subprocess.run(
        ("git", "show", f"{PARENT_COMMIT}:{source.relative_to(repo).as_posix()}"),
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout
    if source.read_bytes() != published:
        raise RuntimeError("R14R2R1 preparer differs from published parent bytes")
    spec = importlib.util.spec_from_file_location("r14r2r1_prepare_assets", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load authenticated R14R2R1 preparer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def transform_admission(path: Path) -> None:
    text = path.read_text()
    text = replace_once(text, "import os\n", "import os\nimport re\n", "admission import")
    old = '''    gates = {
        "all_partition_active_allocation_absent": active == [],
        "capture_bounded_seconds": (finished - started).total_seconds() <= 15,
        "exact_node": len(sinfo) == 1 and sinfo[0].split("|", 1)[0] == "node03",
        "four_l40_inventory": len(sinfo) == 1 and "gpu:l40:4" in sinfo[0].lower(),
        "node_idle": len(sinfo) == 1 and sinfo[0].split("|")[1].lower().rstrip("~*+") == "idle",
    }
'''
    new = '''    gpu_pattern = re.compile(r"gres/gpu(?::l40)?:([0-9]+)")
    gpu_matches = [gpu_pattern.search(line.lower()) for line in active]
    active_gpu_count = sum(int(match.group(1)) for match in gpu_matches if match)
    gates = {
        "active_gpu_records_parseable": all(match is not None or "(null)" in line.lower() for line, match in zip(active, gpu_matches, strict=True)),
        "at_least_two_l40_idle": active_gpu_count <= 2,
        "capture_bounded_seconds": (finished - started).total_seconds() <= 15,
        "exact_node": len(sinfo) == 1 and sinfo[0].split("|", 1)[0] == "node03",
        "four_l40_inventory": len(sinfo) == 1 and "gpu:l40:4" in sinfo[0].lower(),
    }
'''
    text = replace_once(text, old, new, "admission occupancy gates")
    text = text.replace("node03 immediate four-L40 occupancy gate failed", "node03 immediate two-L40 availability gate failed")
    text = text.replace('"immediate_node03_four_l40_idle"', '"immediate_node03_two_l40_available"')
    text = text.replace('"active_allocations": active,', '"active_allocations": active,\n        "active_gpu_count": active_gpu_count,')
    path.write_text(text)


def transform_launcher(path: Path) -> None:
    text = path.read_text()
    text = text.replace("Launch and aggregate four isolated R14 single-GPU candidate processes.", "Launch four isolated candidates as two deterministic two-GPU waves.")
    old_tuples = '''    expected_tuples = [
        (0, 0, expected_roles[0], "centered_location_ou", "K2"),
        (1, 1, expected_roles[1], "centered_location_ou_smooth_climatology", "K2"),
        (2, 2, expected_roles[2], "centered_location_and_scale_ou", "K2"),
        (3, 3, expected_roles[3], "centered_location_and_scale_ou_smooth_climatology", "K2"),
    ]
'''
    new_tuples = '''    expected_tuples = [
        (0, 0, 0, expected_roles[0], "centered_location_ou", "K2"),
        (0, 1, 1, expected_roles[1], "centered_location_ou_smooth_climatology", "K2"),
        (1, 2, 0, expected_roles[2], "centered_location_and_scale_ou", "K2"),
        (1, 3, 1, expected_roles[3], "centered_location_and_scale_ou_smooth_climatology", "K2"),
    ]
'''
    text = replace_once(text, old_tuples, new_tuples, "launcher tuple map")
    text = replace_once(
        text,
        '''        and role_map.get("schema_version") == 1
        and role_map.get("expected_accelerator") == "NVIDIA L40"
        and role_map.get("expected_allocated_devices") == 4
        and [(row.get("slot"), row.get("allocation_token_index"), row.get("role"), row.get("candidate"), row.get("capacity")) for row in rows]
''',
        '''        and role_map.get("schema_version") == 2
        and role_map.get("expected_accelerator") == "NVIDIA L40"
        and role_map.get("expected_allocated_devices") == 2
        and role_map.get("waves") == [[0, 1], [2, 3]]
        and [(row.get("wave"), row.get("slot"), row.get("allocation_token_index"), row.get("role"), row.get("candidate"), row.get("capacity")) for row in rows]
''',
        "launcher map gate",
    )
    text = text.replace("len(tokens) == 4", "len(tokens) == 2")
    text = text.replace("allocated_count == 4", "allocated_count == 2")
    text = text.replace("len(devices) == 4", "len(devices) == 2")
    old_launch = '''    processes: list[tuple[dict, subprocess.Popen]] = []
    interrupted = {"signal": None}

    def forward_signal(number, _frame):
        interrupted["signal"] = number
        for _, child in processes:
            if child.poll() is None:
                child.send_signal(number)

    signal.signal(signal.SIGTERM, forward_signal)
    signal.signal(signal.SIGINT, forward_signal)
    if map_ok and allocation_ok and control_ok and paths_ok and shared_read_only and publication_ok:
        for row, token, device, cache_root in zip(rows, tokens, devices, cache_roots):
            for name in ("tmp", "cache", "torch-cache", "pip-cache"):
                (cache_root / name).mkdir(parents=True, exist_ok=False)
            env = os.environ.copy()
            env.update(
                {
                    "CUDA_VISIBLE_DEVICES": token,
                    "PATH": f"{options.environment}/bin:/usr/bin:/bin",
                    "PIP_CACHE_DIR": str(cache_root / "pip-cache"),
                    "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONNOUSERSITE": "1",
                    "TMPDIR": str(cache_root / "tmp"),
                    "TORCH_HOME": str(cache_root / "torch-cache"),
                    "XDG_CACHE_HOME": str(cache_root / "cache"),
                }
            )
            command = [
                str(options.environment / "bin/python"),
                str(options.run_root / "portfolio_candidate_process.py"),
                "--run-root",
                str(options.run_root),
                "--job-local",
                str(options.job_local),
                "--shared-corpus",
                str(options.shared_corpus),
                "--role",
                row["role"],
                "--candidate",
                row["candidate"],
                "--capacity",
                row["capacity"],
                "--slot",
                str(row["slot"]),
                "--allocation-token",
                token,
            ]
            processes.append((row, subprocess.Popen(command, env=env)))

    children = []
    for row, process in processes:
        children.append({"exit_code": process.wait(), "role": row["role"], "slot": row["slot"]})
'''
    new_launch = '''    processes: list[tuple[dict, subprocess.Popen]] = []
    children = []
    interrupted = {"signal": None}

    def forward_signal(number, _frame):
        interrupted["signal"] = number
        for _, child in processes:
            if child.poll() is None:
                child.send_signal(number)

    signal.signal(signal.SIGTERM, forward_signal)
    signal.signal(signal.SIGINT, forward_signal)
    if map_ok and allocation_ok and control_ok and paths_ok and shared_read_only and publication_ok:
        for wave in (0, 1):
            current = []
            for row in [item for item in rows if item["wave"] == wave]:
                token_index = row["allocation_token_index"]
                token = tokens[token_index]
                cache_root = cache_roots[row["slot"]]
                for name in ("tmp", "cache", "torch-cache", "pip-cache"):
                    (cache_root / name).mkdir(parents=True, exist_ok=False)
                env = os.environ.copy()
                env.update(
                    {
                        "CUDA_VISIBLE_DEVICES": token,
                        "PATH": f"{options.environment}/bin:/usr/bin:/bin",
                        "PIP_CACHE_DIR": str(cache_root / "pip-cache"),
                        "PYTHONDONTWRITEBYTECODE": "1",
                        "PYTHONNOUSERSITE": "1",
                        "TMPDIR": str(cache_root / "tmp"),
                        "TORCH_HOME": str(cache_root / "torch-cache"),
                        "XDG_CACHE_HOME": str(cache_root / "cache"),
                    }
                )
                command = [
                    str(options.environment / "bin/python"),
                    str(options.run_root / "portfolio_candidate_process.py"),
                    "--run-root", str(options.run_root),
                    "--job-local", str(options.job_local),
                    "--shared-corpus", str(options.shared_corpus),
                    "--role", row["role"],
                    "--candidate", row["candidate"],
                    "--capacity", row["capacity"],
                    "--slot", str(row["slot"]),
                    "--allocation-token", token,
                ]
                process = subprocess.Popen(command, env=env)
                processes.append((row, process))
                current.append((row, process))
            for row, process in current:
                children.append({"exit_code": process.wait(), "role": row["role"], "slot": row["slot"], "wave": wave})
            if any(item["exit_code"] != 0 for item in children if item["wave"] == wave):
                break
'''
    text = replace_once(text, old_launch, new_launch, "launcher process block")
    text = text.replace('tokens[row["slot"]]', 'tokens[row["allocation_token_index"]]')
    text = text.replace('"exact_four_l40_allocation": allocation_ok', '"exact_two_l40_allocation": allocation_ok')
    text = text.replace('"unique_child_binding_tokens": len(tokens) == 2 and len(set(tokens)) == 4', '"two_unique_wave_binding_tokens": len(tokens) == 2 and len(set(tokens)) == 2')
    text = text.replace('"all_children_reaped": len(children) == 4,', '"all_children_reaped": len(children) == 4,\n        "two_complete_nonoverlapping_waves": [item.get("wave") for item in children] == [0, 0, 1, 1],')
    path.write_text(text)


def prepare(r14r2_assets: Path, package: Path, source_commit: str, output: Path, *, require_published: bool) -> dict:
    repo = package.parents[2]
    parent = load_parent(repo)
    parent_package = repo / "docs/work-packages" / PARENT_PACKAGE_ID
    parent.prepare(r14r2_assets, parent_package, source_commit, output, require_published=require_published)
    parent_manifest_path = output / "asset-manifest.json"
    parent_manifest = json.loads(parent_manifest_path.read_text())
    if not (
        parent_manifest.get("package_id") == PARENT_PACKAGE_ID
        and parent_manifest.get("source_commit") == source_commit
        and parent_manifest.get("protected_roles_opened") == []
    ):
        raise RuntimeError("reconstructed R14R2R1 authority drift")
    parent_manifest_path.unlink()
    source_paths = {
        name: item["source_path"]
        for name, item in parent_manifest["assets"].items()
        if isinstance(item.get("source_path"), str)
    }
    for name in IDENTITY_REWRITES:
        path = output / name
        text = path.read_text().replace(PARENT_PACKAGE_ID, PACKAGE_ID).replace(PARENT_RUN_ID, RUN_ID)
        text = text.replace(PARENT_RECORD, RECORD).replace("a10m5r14r2r1-precleanup-replay", "a10m5r14r2r2-precleanup-replay")
        text = text.replace("a10m5r14r2r1-immediate-pre-submit-occupancy", "a10m5r14r2r2-immediate-pre-submit-occupancy")
        path.write_text(text)
        source_paths.pop(name, None)
    transform_admission(output / "admission_checker.py")
    transform_launcher(output / "portfolio_launcher.py")
    for name, relative in OVERLAYS.items():
        source = package / relative
        repo_relative = source.relative_to(repo).as_posix()
        data = (
            subprocess.run(("git", "show", f"{source_commit}:{repo_relative}"), cwd=repo, check=True, capture_output=True).stdout
            if require_published
            else source.read_bytes()
        )
        (output / name).write_bytes(data)
        source_paths[name] = repo_relative
    for path in output.iterdir():
        if path.is_file() and path.suffix in {".py", ".sh"}:
            path.chmod(0o700)
    changed = {
        name
        for name, expected in parent_manifest["assets"].items()
        if identity(output / name)
        != {key: expected[key] for key in ("bytes", "sha256")}
    }
    expected_changed = IDENTITY_REWRITES | set(OVERLAYS)
    if changed != expected_changed:
        raise RuntimeError(f"R14R2R2 operational changed-file roster drift: {sorted(changed)}")
    for name in IDENTITY_REWRITES:
        text = (output / name).read_text()
        if PARENT_RUN_ID in text or PARENT_RECORD in text:
            raise RuntimeError(f"stale R14R2R1 execution identity remains: {name}")
    assets = {}
    for path in sorted(output.iterdir()):
        if path.is_file():
            assets[path.name] = {
                **identity(path),
                **({"source_path": source_paths[path.name]} if path.name in source_paths else {}),
            }
    manifest = {
        "assets": assets,
        "canonical_configuration_id": parent_manifest["canonical_configuration_id"],
        "canonical_configuration_semantic_sha256": parent_manifest["canonical_configuration_semantic_sha256"],
        "checker_assets": parent_manifest["checker_assets"],
        "package_id": PACKAGE_ID,
        "parent_package_id": PARENT_PACKAGE_ID,
        "protected_roles_opened": [],
        "schema_version": 1,
        "source_commit": source_commit,
        "toolkit_prerequisite_commit": TOOLKIT_COMMIT,
        "two_wave_schedule": [[0, 1], [2, 3]],
    }
    (output / "asset-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--r14r2-assets", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    if re.fullmatch(r"[0-9a-f]{40}", options.source_commit) is None:
        raise RuntimeError("full source commit required")
    prepare(options.r14r2_assets, options.package, options.source_commit, options.output, require_published=True)


if __name__ == "__main__":
    main()
