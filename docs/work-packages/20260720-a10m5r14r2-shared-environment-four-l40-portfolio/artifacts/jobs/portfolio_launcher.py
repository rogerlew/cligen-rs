#!/usr/bin/env python3
"""Launch and aggregate four isolated R14 single-GPU candidate processes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
from pathlib import Path


PORTFOLIO_ROLE = "continuous-distribution-head-factorial-portfolio"


def digest_tree(root: Path) -> str:
    value = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        value.update(path.relative_to(root).as_posix().encode())
        value.update(b"\0")
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                value.update(block)
    return value.hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    semantic = dict(value)
    semantic.pop("record_sha256", None)
    semantic["record_sha256"] = hashlib.sha256(
        json.dumps(semantic, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    temporary = path.with_suffix(path.suffix + ".promote")
    temporary.write_text(json.dumps(semantic, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def authenticated(value: dict) -> bool:
    semantic = dict(value)
    recorded = semantic.pop("record_sha256", None)
    return recorded == hashlib.sha256(
        json.dumps(semantic, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--job-local", type=Path, required=True)
    parser.add_argument("--environment", type=Path, required=True)
    parser.add_argument("--shared-corpus", type=Path, required=True)
    parser.add_argument("--role-map", type=Path, required=True)
    options = parser.parse_args()

    portfolio_output = options.run_root / "results" / PORTFOLIO_ROLE
    role_map = json.loads(options.role_map.read_text(encoding="utf-8"))
    manifest = json.loads((options.run_root / "asset-manifest.json").read_text())
    map_identity = {
        "bytes": options.role_map.stat().st_size,
        "sha256": hashlib.sha256(options.role_map.read_bytes()).hexdigest(),
    }
    map_authenticated = map_identity == {
        key: manifest.get("assets", {}).get("portfolio-role-map.json", {}).get(key)
        for key in ("bytes", "sha256")
    }
    rows = role_map.get("processes", [])
    tokens = os.environ.get("CUDA_VISIBLE_DEVICES", "").split(",")
    tokens = [token.strip() for token in tokens if token.strip()]

    import torch

    allocated_count = torch.cuda.device_count()
    devices = []
    for index in range(allocated_count):
        devices.append({"index": index, "name": torch.cuda.get_device_name(index)})

    expected_roles = [
        "continuous-location-ou-k2",
        "continuous-location-ou-smooth-climatology-k2",
        "continuous-location-scale-ou-k2",
        "continuous-location-scale-ou-smooth-climatology-k2",
    ]
    expected_tuples = [
        (0, 0, expected_roles[0], "centered_location_ou", "K2"),
        (1, 1, expected_roles[1], "centered_location_ou_smooth_climatology", "K2"),
        (2, 2, expected_roles[2], "centered_location_and_scale_ou", "K2"),
        (3, 3, expected_roles[3], "centered_location_and_scale_ou_smooth_climatology", "K2"),
    ]
    map_ok = (
        map_authenticated
        and role_map.get("schema_version") == 1
        and role_map.get("expected_accelerator") == "NVIDIA L40"
        and role_map.get("expected_allocated_devices") == 4
        and [(row.get("slot"), row.get("allocation_token_index"), row.get("role"), row.get("candidate"), row.get("capacity")) for row in rows]
        == expected_tuples
    )
    allocation_ok = (
        len(tokens) == 4
        and len(set(tokens)) == 4
        and allocated_count == 4
        and len(devices) == 4
        and all(row["name"] == "NVIDIA L40" for row in devices)
    )
    control_path = options.run_root / "results/control-materialization/evidence.json"
    controls = json.loads(control_path.read_text())
    setup = json.loads((portfolio_output / "setup.json").read_text())
    admission_path = options.run_root / "admissions" / f"{PORTFOLIO_ROLE}.json"
    admission = json.loads(admission_path.read_text())
    admission_sha = hashlib.sha256(admission_path.read_bytes()).hexdigest()
    setup_execution = setup.get("execution_identity", {})
    setup_identities = setup.get("identities", {})
    admission_ok = (
        authenticated(admission)
        and admission.get("record_type") == "a10m5r14r2-submission-admission"
        and admission.get("package_id")
        == "20260720-a10m5r14r2-shared-environment-four-l40-portfolio"
        and admission.get("run_id") == options.run_root.name
        and admission.get("role") == PORTFOLIO_ROLE
        and admission.get("source_commit") == manifest.get("source_commit")
        and admission.get("asset_manifest_sha256")
        == hashlib.sha256((options.run_root / "asset-manifest.json").read_bytes()).hexdigest()
        and admission.get("valid") is True
        and admission.get("decision") == "PASS"
        and isinstance(admission.get("gates"), dict)
        and bool(admission["gates"])
        and all(admission["gates"].values())
    )
    control_ok = (
        hashlib.sha256(control_path.read_bytes()).hexdigest()
        == admission.get("input_identities", {}).get("control_gate_receipt_sha256")
        and controls.get("valid") is True
        and controls.get("protected_roles_opened") == []
        and isinstance(controls.get("gates"), dict)
        and bool(controls["gates"])
        and all(controls["gates"].values())
    )
    setup_ok = (
        authenticated(setup)
        and setup.get("valid") is True
        and setup.get("ready_for_science") is True
        and isinstance(setup.get("authentication"), dict)
        and bool(setup["authentication"])
        and all(setup["authentication"].values())
        and setup_execution.get("asset_manifest_sha256")
        == hashlib.sha256((options.run_root / "asset-manifest.json").read_bytes()).hexdigest()
        and setup_execution.get("run_id") == options.run_root.name
        and setup_execution.get("role") == PORTFOLIO_ROLE
        and setup_execution.get("job_id") == os.environ.get("SLURM_JOB_ID")
        and setup_execution.get("node") == "node03"
        and setup_execution.get("source_commit") == manifest.get("source_commit")
        and setup_execution.get("submission_admission_record_sha256")
        == admission.get("record_sha256")
        and setup_identities.get("submission_admission", {}).get("sha256")
        == admission_sha
        and setup_identities.get("asset_manifest", {}).get("sha256")
        == hashlib.sha256((options.run_root / "asset-manifest.json").read_bytes()).hexdigest()
    )
    publication = {
        "asset_manifest_sha256": hashlib.sha256(
            (options.run_root / "asset-manifest.json").read_bytes()
        ).hexdigest(),
        "run_id": options.run_root.name,
        "source_commit": manifest.get("source_commit"),
        "submission_admission_record_sha256": setup.get("execution_identity", {}).get(
            "submission_admission_record_sha256"
        ),
    }
    publication_ok = (
        setup_ok
        and admission_ok
        and all(isinstance(value, str) and value for value in publication.values())
    )
    output_roots = [options.run_root / "results" / role for role in expected_roles]
    cache_roots = [options.job_local / "processes" / role for role in expected_roles]
    paths_ok = (
        len({str(path.resolve()) for path in output_roots}) == 4
        and len({str(path.resolve()) for path in cache_roots}) == 4
        and not any(path.exists() for path in output_roots + cache_roots)
    )
    shared_before = {
        "corpus_sha256": digest_tree(options.shared_corpus),
        "environment_sha256": digest_tree(options.environment),
    }
    shared_read_only = all(
        path.stat().st_mode & 0o222 == 0
        for root in (options.environment, options.shared_corpus)
        for path in [root, *(item for item in root.rglob("*") if not item.is_symlink())]
    )

    processes: list[tuple[dict, subprocess.Popen]] = []
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
    shared_after = {
        "corpus_sha256": digest_tree(options.shared_corpus),
        "environment_sha256": digest_tree(options.environment),
    }
    role_evidence = []
    for role in expected_roles:
        path = options.run_root / "results" / role / "evidence.json"
        role_evidence.append(json.loads(path.read_text()) if path.exists() else {"role": role, "valid": False})
    exact_role_evidence = map_ok and allocation_ok and len(role_evidence) == 4
    for row, evidence in zip(rows if exact_role_evidence else [], role_evidence):
        process_path = options.run_root / "results" / row["role"] / "process.json"
        process = json.loads(process_path.read_text()) if process_path.exists() else {}
        exact_role_evidence = exact_role_evidence and (
            authenticated(process)
            and authenticated(evidence)
            and process.get("role") == row["role"]
            and process.get("slot") == row["slot"]
            and process.get("candidate") == row["candidate"]
            and process.get("capacity") == row["capacity"]
            and process.get("allocation_token") == tokens[row["slot"]]
            and all(process.get(key) == value for key, value in publication.items())
            and process.get("valid") is True
            and evidence.get("role") == row["role"]
            and evidence.get("slot") == row["slot"]
            and evidence.get("candidate_id") == row["candidate"]
            and evidence.get("capacity_id") == row["capacity"]
            and evidence.get("protected_roles_opened") == []
            and all(evidence.get(key) == value for key, value in publication.items())
            and evidence.get("valid") is True
        )
    gates = {
        "all_children_launched": len(processes) == 4,
        "all_children_reaped": len(children) == 4,
        "all_process_exits_zero": len(children) == 4 and all(row["exit_code"] == 0 for row in children),
        "all_role_evidence_authenticated": exact_role_evidence,
        "control_authenticated": control_ok,
        "portfolio_admission_authenticated": admission_ok,
        "disjoint_output_and_cache_roots": paths_ok,
        "exact_four_l40_allocation": allocation_ok,
        "exact_authenticated_role_map": map_ok,
        "publication_identity_authenticated": publication_ok,
        "setup_record_authenticated": setup_ok,
        "shared_trees_immutable": shared_read_only and shared_before == shared_after,
        "signal_free_completion": interrupted["signal"] is None,
        "unique_child_binding_tokens": len(tokens) == 4 and len(set(tokens)) == 4,
    }
    launcher = {
        "allocation_tokens": tokens,
        "children": children,
        "devices": devices,
        "gates": gates,
        "protected_roles_opened": [],
        "role": PORTFOLIO_ROLE,
        "schema_version": 1,
        "signal": interrupted["signal"],
        "shared_after": shared_after,
        "shared_before": shared_before,
        "role_map_identity": map_identity,
        "publication_identity": publication,
        "valid": bool(gates) and all(gates.values()),
    }
    atomic_json(portfolio_output / "launcher.json", launcher)
    return 0 if launcher["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
