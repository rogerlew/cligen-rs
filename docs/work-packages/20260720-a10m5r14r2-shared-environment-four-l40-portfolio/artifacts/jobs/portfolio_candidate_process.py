#!/usr/bin/env python3
"""Run one frozen R14 candidate in an isolated single-GPU process."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def canonical(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode()


def atomic_json(path: Path, value: dict) -> None:
    semantic = dict(value)
    semantic.pop("record_sha256", None)
    semantic["record_sha256"] = hashlib.sha256(canonical(semantic)).hexdigest()
    temporary = path.with_suffix(path.suffix + ".promote")
    temporary.write_text(json.dumps(semantic, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def authenticate_training(path: Path, candidate: str, capacity: str) -> dict:
    """Promote the frozen writer's plain JSON without changing its science fields."""
    training = json.loads(path.read_text(encoding="utf-8"))
    if not (
        training.get("architecture") == candidate
        and training.get("capacity") == capacity
        and training.get("schema_version") == 1
        and isinstance(training.get("seeds"), list)
        and bool(training["seeds"])
    ):
        raise RuntimeError("frozen training publication shape drift")
    atomic_json(path, training)
    promoted = json.loads(path.read_text(encoding="utf-8"))
    semantic = dict(promoted)
    recorded = semantic.pop("record_sha256", None)
    if recorded != hashlib.sha256(canonical(semantic)).hexdigest():
        raise RuntimeError("training publication authentication failed")
    return promoted


def bounded_stderr(source: Path, target: Path, replacements: tuple[tuple[str, str], ...]) -> None:
    raw = source.read_text(encoding="utf-8", errors="replace") if source.exists() else ""
    for old, new in replacements:
        raw = raw.replace(old, new)
    target.write_text(raw[-65536:], encoding="utf-8")
    source.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--job-local", type=Path, required=True)
    parser.add_argument("--shared-corpus", type=Path, required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--capacity", required=True)
    parser.add_argument("--slot", type=int, required=True)
    parser.add_argument("--allocation-token", required=True)
    options = parser.parse_args()

    output = options.run_root / "results" / options.role
    output.mkdir(parents=True, exist_ok=False)
    stderr_part = output / "candidate.stderr.part"
    process_record = output / "process.json"
    science_part = output / "evidence.json.part"
    final_evidence = output / "evidence.json"
    manifest_path = options.run_root / "asset-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    setup = json.loads(
        (
            options.run_root
            / "results/continuous-distribution-head-factorial-portfolio/setup.json"
        ).read_text()
    )
    publication = {
        "asset_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "run_id": options.run_root.name,
        "source_commit": manifest.get("source_commit"),
        "submission_admission_record_sha256": setup.get("execution_identity", {}).get(
            "submission_admission_record_sha256"
        ),
    }

    import torch

    visible_count = torch.cuda.device_count()
    device_name = torch.cuda.get_device_name(0) if visible_count == 1 else None
    binding_ok = (
        visible_count == 1
        and device_name == "NVIDIA L40"
        and os.environ.get("CUDA_VISIBLE_DEVICES") == options.allocation_token
    )

    command = [
        sys.executable,
        str(options.run_root / "continuous_candidate_experiment.py"),
        "--run-root",
        str(options.run_root),
        "--corpus",
        str(options.shared_corpus),
        "--controls",
        str(options.run_root / "results/control-materialization"),
        "--candidate",
        options.candidate,
        "--capacity",
        options.capacity,
        "--output",
        str(output),
    ]
    exit_code = 126
    if binding_ok:
        with stderr_part.open("wb") as stderr:
            exit_code = subprocess.run(command, stderr=stderr, check=False).returncode
    else:
        stderr_part.write_text("single-L40 binding authentication failed\n")

    bounded_stderr(
        stderr_part,
        output / "candidate.stderr",
        (
            (str(options.run_root), "[REMOTE_RUN_ROOT]"),
            (str(options.job_local), "[JOB_LOCAL]"),
        ),
    )
    training = None
    if exit_code == 0:
        try:
            training = authenticate_training(
                output / "training.json", options.candidate, options.capacity
            )
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as error:
            exit_code = 125
            with (output / "candidate.stderr").open("a", encoding="utf-8") as stream:
                stream.write(f"training publication promotion failed: {error}\n")
    science = {}
    if science_part.exists():
        science = json.loads(science_part.read_text(encoding="utf-8"))
    science_gates = science.get("gates", {})
    science_valid = (
        exit_code == 0
        and isinstance(science_gates, dict)
        and bool(science_gates)
        and all(value is True for value in science_gates.values())
    )
    process = {
        "allocation_token": options.allocation_token,
        "candidate": options.candidate,
        "capacity": options.capacity,
        "device_name": device_name,
        "exit_code": exit_code,
        "gates": {
            "candidate_identity": output.name == options.role,
            "exact_single_visible_device": visible_count == 1,
            "expected_allocation_token": os.environ.get("CUDA_VISIBLE_DEVICES")
            == options.allocation_token,
            "l40_identity": device_name == "NVIDIA L40",
            "science_evidence_complete": science_valid,
            "training_record_authenticated": training is not None,
        },
        "protected_roles_opened": [],
        "role": options.role,
        "schema_version": 1,
        "slot": options.slot,
        "training_record_sha256": (
            training.get("record_sha256") if training is not None else None
        ),
        **publication,
    }
    process["valid"] = exit_code == 0 and all(process["gates"].values())
    atomic_json(process_record, process)

    evidence = dict(science)
    evidence.pop("record_sha256", None)
    evidence.setdefault("protected_roles_opened", [])
    gates = evidence.setdefault("gates", {})
    gates.update(
        {
            "isolated_process_binding": process["valid"],
            "process_exit_zero": exit_code == 0,
            "process_receipt_published": process_record.is_file(),
            "training_record_authenticated": training is not None,
        }
    )
    evidence.update(
        {
            "candidate_id": options.candidate,
            "capacity_id": options.capacity,
            "exit_code": exit_code,
            "role": options.role,
            "schema_version": 1,
            "slot": options.slot,
            "training_record_sha256": (
                training.get("record_sha256") if training is not None else None
            ),
            **publication,
        }
    )
    evidence["valid"] = exit_code == 0 and bool(gates) and all(gates.values())
    evidence["verdict"] = "PASS" if evidence["valid"] else "FAIL"
    atomic_json(final_evidence, evidence)
    science_part.unlink(missing_ok=True)
    return 0 if evidence["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
