#!/usr/bin/env python3
"""Build fresh control-only calibration authority and semantic plan records."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[2]
REPO = PACKAGE.parents[2]
PARENT_COMMIT = "b38f695697a8636e67f041ccae373107cb5cb5bc"
SOURCE = (
    PACKAGE.parent
    / "20260721-a10m5r15r2-external-normal-conditioning-execution"
    / "artifacts/jobs/build_control_records.py"
)
PACKAGE_ID = "20260722-a10m5r15r2r1-successor-control-identity-calibration"
RUN_ID = "a10m5r15r2r1-successor-control-identity-calibration-r1"
RECORD_TYPE = "a10m5r15r2r1-submission-admission"
PARENT_PACKAGE = SOURCE.parents[2]
FAILURE = PARENT_PACKAGE / "artifacts/execution-r0-failure.json"
CONTRACT = PACKAGE / "artifacts/control-calibration-contract.json"
CALIBRATION_ABORT = PACKAGE / "artifacts/execution-r0-abort.json"
CONTROL_ROLE = "control-materialization"
CONTROL_EVIDENCE = [
    "admissions/control-materialization.json",
    "recovery.json",
    "results/control-materialization/calendar-preflight.json",
    "results/control-materialization/control-identity.json",
    "results/control-materialization/control-summary.json",
    "results/control-materialization/evidence.json",
    "results/control-materialization/setup.json",
    "results/control-materialization/setup.log",
    "results/control-materialization/supervisor.json",
    "slurm/control-materialization.0.err",
    "slurm/control-materialization.0.out",
    "slurm/toolkit-recovery.0.err",
    "slurm/toolkit-recovery.0.out",
]
EXPECTED_CONTRACT = {
    "package_id": PACKAGE_ID,
    "parent_asset_manifest_sha256": "64a5595fab4b493c5985db3e0a271ec6eeaa7d2dcdbe77c10e7f97d5474f988b",
    "successor_corpus_sha256": "7b41e497d215c85ae734dea438424f23ae01cff59a3b3ba55ec32442578553f2",
}
EXPECTED_IDENTITY_CONTRACT = {
    "gating_fields": [
        "capacity_id",
        "checkpoint_epoch",
        "checkpoint_global_step",
        "checkpoint_payload_bytes",
        "checkpoint_payload_sha256",
        "corpus_cursor_epoch_order_sha256",
        "corpus_cursor_next_batch",
        "family",
        "hidden_size",
        "model_record_sha256",
        "parameter_count",
        "row_id",
        "training_seed",
        "validation_primary_nll",
        "validation_stability",
        "validation_tail_score",
    ],
    "non_gating_provenance_fields": [
        "checkpoint_record_sha256",
        "export_metadata_sha256",
        "export_sha256",
    ],
    "required_row_count": 6,
}


def git_bytes(commit: str, path: Path) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path.relative_to(REPO).as_posix()}"),
        cwd=REPO,
        check=True,
        capture_output=True,
    ).stdout


if SOURCE.read_bytes() != git_bytes(PARENT_COMMIT, SOURCE):
    raise RuntimeError("R2 control-record builder differs from published bytes")
spec = importlib.util.spec_from_file_location("r15r2_control_records", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError("cannot load authenticated R2 control-record builder")
parent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parent
spec.loader.exec_module(parent)
inherited = parent.inherited
base_authority = parent.authority
base_plan = parent.plan
base_calibration_bundle = parent.calibration_bundle


def calibration_bundle(record_commit: str | None = None) -> dict:
    """Keep the valid R2 attribution receipt bound to its owning package."""
    active_package = parent.PACKAGE_ID
    parent.PACKAGE_ID = PARENT_PACKAGE.name
    try:
        return base_calibration_bundle(record_commit)
    finally:
        parent.PACKAGE_ID = active_package


def failure_projection(value: dict) -> dict:
    control = value["control"]
    evidence = value["evidence_chain"]
    return {
        "actual_checkpoint_payload_sha256": control[
            "actual_checkpoint_payload_sha256"
        ],
        "cleanup_record_sha256": evidence["cleanup_record_sha256"],
        "collection_record_sha256": evidence["collection_record_sha256"],
        "expected_checkpoint_payload_sha256": control[
            "expected_checkpoint_payload_sha256"
        ],
        "gate_receipt_sha256": control["gate_receipt_sha256"],
        "job_id": str(control["job_id"]),
        "job_receipt_record_sha256": control["job_receipt_record_sha256"],
        "matrix_stop_record_sha256": value["matrix_stop"]["record_sha256"],
        "plan_id": value["plan_id"],
        "row_id": control["row_id"],
        "run_id": value["run_id"],
        "sanitized_control_stderr_sha256": evidence[
            "sanitized_control_stderr_sha256"
        ],
        "source_commit": value["source_commit"],
        "terminal_record_sha256": value["terminal_record_sha256"],
    }


def validate_contract(path: Path, failure: dict) -> None:
    contract = json.loads(path.read_text(encoding="utf-8"))
    if not (
        all(contract.get(key) == value for key, value in EXPECTED_CONTRACT.items())
        and contract.get("schema_version") == 1
        and contract.get("candidate_output_allowed") is False
        and contract.get("protected_roles_opened") == []
        and contract.get("maximum_l40_minutes") == 35
        and contract.get("control_capacities") == ["P1", "P2"]
        and contract.get("control_seeds") == [147031, 271828, 314159]
        and contract.get("identity_contract") == EXPECTED_IDENTITY_CONTRACT
        and contract.get("parent_failure") == failure_projection(failure)
    ):
        raise RuntimeError("control calibration contract identity drift")


def validate_execution_contract(asset_root: Path, source_commit: str) -> None:
    staged = asset_root / "control-calibration-contract.json"
    repository_bytes = CONTRACT.read_bytes()
    if not (
        staged.read_bytes() == repository_bytes
        and git_bytes(source_commit, CONTRACT) == repository_bytes
    ):
        raise RuntimeError("staged, repository, and published contract differ")
    validate_contract(staged, json.loads(FAILURE.read_text(encoding="utf-8")))


def failure_bundle(record_commit: str | None = None) -> dict:
    package_path = PARENT_PACKAGE / "package.md"
    disposition_path = PARENT_PACKAGE / "disposition.md"
    if (
        "Status: `EXECUTED-HOLD-SUCCESSOR-CONTROL-IDENTITY`"
        not in package_path.read_text(encoding="utf-8")
    ):
        raise RuntimeError("R2 failure terminal drift")
    failure = json.loads(FAILURE.read_text(encoding="utf-8"))
    validate_contract(CONTRACT, failure)
    if not (
        failure.get("record_authenticated") is True
        and failure.get("record_valid") is True
        and failure.get("scientific_interpretation_allowed") is False
        and failure.get("terminal") == "LEMHI-TOOLKIT-RUN-CLOSED"
        and failure.get("actual_gpu_minutes") == 8
        and failure.get("protected_roles_opened") == []
        and all(
            isinstance(value, str) and len(value) == 64
            for value in (
                failure.get("control", {}).get("job_receipt_record_sha256"),
                failure.get("control", {}).get("gate_receipt_sha256"),
                failure.get("matrix_stop", {}).get("record_sha256"),
                failure.get("evidence_chain", {}).get(
                    "collection_record_sha256"
                ),
                failure.get("evidence_chain", {}).get("cleanup_record_sha256"),
                failure.get("terminal_record_sha256"),
                failure.get("evidence_chain", {}).get(
                    "sanitized_control_stderr_sha256"
                ),
            )
        )
    ):
        raise RuntimeError("R2 failure evidence invalid")
    files = {
        path.relative_to(REPO).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": inherited.digest(path),
        }
        for path in (package_path, disposition_path, FAILURE)
    }
    if record_commit is not None:
        for relative in files:
            if git_bytes(record_commit, REPO / relative) != (REPO / relative).read_bytes():
                raise RuntimeError("R2 failure evidence differs from published source")
    return {
        "files": files,
        "package_id": PARENT_PACKAGE.name,
        "record_commit": record_commit,
        "terminal": "EXECUTED-HOLD-SUCCESSOR-CONTROL-IDENTITY",
    }


def abort_bundle(record_commit: str | None = None) -> dict:
    value = json.loads(CALIBRATION_ABORT.read_text(encoding="utf-8"))
    if not (
        value.get("record_type") == "abort_receipt"
        and value.get("record_sha256")
        == "6ac0b6ad0c921febb3aeb94bcd33e0faaab44b4e30a413d7816df5528c6eb057"
        and value.get("run_id")
        == "a10m5r15r2r1-successor-control-identity-calibration-r0"
        and value.get("source_commit")
        == "c07a7b6cf50114a8709dedc103105994ae67b6eb"
        and value.get("remote_absent") is True
        and value.get("job_local_cleanup") == "not_started"
        and value.get("terminal")
        == "LEMHI-TOOLKIT-RUN-ABORTED-BEFORE-SUBMISSION"
    ):
        raise RuntimeError("calibration r0 abort evidence drift")
    if (
        record_commit is not None
        and git_bytes(record_commit, CALIBRATION_ABORT) != CALIBRATION_ABORT.read_bytes()
    ):
        raise RuntimeError("calibration r0 abort differs from published source")
    return {
        "bytes": CALIBRATION_ABORT.stat().st_size,
        "record_commit": record_commit,
        "record_sha256": value["record_sha256"],
        "sha256": inherited.digest(CALIBRATION_ABORT),
    }


def authority(options) -> None:
    failure_bundle(options.source_commit)
    abort_bundle(options.source_commit)
    validate_execution_contract(options.asset_root, options.source_commit)
    base_authority(options)
    value = json.loads(options.output.read_text(encoding="utf-8"))
    value.update(
        {
            "package_id": PACKAGE_ID,
            "calibration_predecessor_run_evidence": abort_bundle(
                options.source_commit
            ),
            "operational_predecessor_package_evidence": failure_bundle(
                options.source_commit
            ),
            "predecessor_package_evidence": failure_bundle(),
            "resource_ceiling_gpu_minutes": 35,
            "resource_class": "one-control-successor-identity-calibration",
            "successor_control_calibration_contract": {
                "bytes": (options.asset_root / "control-calibration-contract.json").stat().st_size,
                "sha256": inherited.digest(
                    options.asset_root / "control-calibration-contract.json"
                ),
            },
        }
    )
    inherited.write(options.output, value)


def plan(options) -> None:
    failure_bundle(options.source_commit)
    abort_bundle(options.source_commit)
    validate_execution_contract(options.asset_root, options.source_commit)
    base_plan(options)
    value = json.loads(options.output.read_text(encoding="utf-8"))
    value["package_id"] = PACKAGE_ID
    value["run_id"] = RUN_ID
    value["calibration_predecessor_run_evidence"] = abort_bundle(
        options.source_commit
    )
    value["operational_predecessor_package_evidence"] = failure_bundle(
        options.source_commit
    )
    value["predecessor_package_evidence"] = failure_bundle()
    value["jobs"] = [
        job for job in value["jobs"] if job.get("role") == CONTROL_ROLE
    ]
    if len(value["jobs"]) != 1:
        raise RuntimeError("control-only job projection failed")
    value["submission_waves"] = [[CONTROL_ROLE]]
    value["admission_materialization"]["record_type"] = RECORD_TYPE
    value["admission_materialization"]["required_roles"] = [CONTROL_ROLE]
    value["evidence_allowlist"] = CONTROL_EVIDENCE
    value["evidence_volume"]["maximum_files"] = len(CONTROL_EVIDENCE)
    value["candidate_output_allowed"] = False
    value["successor_control_calibration_contract"] = {
        "bytes": (options.asset_root / "control-calibration-contract.json").stat().st_size,
        "sha256": inherited.digest(
            options.asset_root / "control-calibration-contract.json"
        ),
    }
    value["control_role_map"] = {
        "bytes": (options.asset_root / "control-role-map.json").stat().st_size,
        "sha256": inherited.digest(options.asset_root / "control-role-map.json"),
    }
    value.pop("immediate_pre_submit_occupancy", None)
    inherited.write(options.output, value)


parent.PACKAGE_ID = PACKAGE_ID
parent.RUN_ID = RUN_ID
parent.RECORD_TYPE = RECORD_TYPE
parent.predecessor_bundle = failure_bundle
parent.calibration_bundle = calibration_bundle
inherited.PACKAGE_ID = PACKAGE_ID
inherited.PACKAGE = PACKAGE
inherited.RUN_ID = RUN_ID
inherited.AUTHORITY_ID = f"{RUN_ID}-authority"
inherited.BUDGET_ID = f"{RUN_ID}-budget"
inherited.AUTHORITY_TOKEN = f"{RUN_ID}-authority-token"
inherited.PREDECESSOR_COMMIT = PARENT_COMMIT
inherited.predecessor_bundle = failure_bundle
inherited.operational_predecessor_bundle = failure_bundle
inherited.authority = authority
inherited.plan = plan
parent.authority = authority
parent.plan = plan


if __name__ == "__main__":
    inherited.main()
