#!/usr/bin/env python3
"""Verify the successor control-calibration scaffold fails closed."""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent.parent
REPO = PACKAGE.parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from research.a10.lemhi_toolkit.core import read_record


R2 = PACKAGE.parent / "20260721-a10m5r15r2-external-normal-conditioning-execution"
CONTRACT = PACKAGE / "artifacts/control-calibration-contract.json"
ROLE_MAP = PACKAGE / "artifacts/control-role-map.json"
CORPUS_PIN = PACKAGE / "artifacts/corpus-layout-pin.json"
CORPUS_VERIFIER = PACKAGE / "artifacts/verify_corpus_layout.py"
FAILURE = R2 / "artifacts/execution-r0-failure.json"
ABORTS = (
    PACKAGE / "artifacts/execution-r0-abort.json",
    PACKAGE / "artifacts/execution-r1-abort.json",
)
DIAGNOSTICS = PACKAGE / "artifacts/pre-submission-diagnostics.json"
JOBS = PACKAGE / "artifacts/jobs"
EXPECTED_CHAIN = {
    "cleanup_record_sha256": "4365bbdef1910a0600c4347947aff92f4f71ba9fe174854b82ea80393ca60d3b",
    "collection_record_sha256": "55d333eb9300f8342d76c6757f5e710aec0547993e7276e68010e7627383ed41",
    "gate_receipt_sha256": "fb4a0b14759276d505133e5f8493b43efb44903fb698df01425647785107bb4a",
    "job_receipt_record_sha256": "a7fdc4b67d927d1f70cde72a81efc0fdce3d46cc60d74cde279c253976224b7d",
    "matrix_stop_record_sha256": "39eb154dc1533ff6a8381d7fdedbb3f179f88e67e779a651d7e068aaa78687ee",
    "sanitized_control_stderr_sha256": "5e6c794a24ccd095ff7293c10b15112a98f03b86b795af6f9e4d985badb82ade",
    "terminal_record_sha256": "459fb9c8def8424c20ed14ed7c2682c4a99a2cebc1cb590df8dcaff24ce02c00",
}
EXPECTED_TOP_LEVEL = {
    "package_id": "20260722-a10m5r15r2r1-successor-control-identity-calibration",
    "parent_asset_manifest_sha256": "64a5595fab4b493c5985db3e0a271ec6eeaa7d2dcdbe77c10e7f97d5474f988b",
    "successor_corpus_sha256": "7b41e497d215c85ae734dea438424f23ae01cff59a3b3ba55ec32442578553f2",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
failure = json.loads(FAILURE.read_text(encoding="utf-8"))
role_map = json.loads(ROLE_MAP.read_text(encoding="utf-8"))
aborts = [read_record(path) for path in ABORTS]
abort_lineage = [
    {
        key: value[key]
        for key in (
            "authority_id",
            "job_local_cleanup",
            "package_id",
            "plan_id",
            "producer_version",
            "record_sha256",
            "record_type",
            "remote_absent",
            "run_id",
            "schema_version",
            "source_commit",
            "terminal",
        )
    }
    for value in aborts
]
if abort_lineage != [
    {
        "authority_id": "a10m5r15r2r1-successor-control-identity-calibration-r0-authority",
        "job_local_cleanup": "not_started",
        "package_id": "20260722-a10m5r15r2r1-successor-control-identity-calibration",
        "plan_id": "037a11f6efb64e7f38601448984861b0f239b2505940bba8c54987d9646dbe17",
        "producer_version": "lemhi-toolkit-hardening-2",
        "record_sha256": "6ac0b6ad0c921febb3aeb94bcd33e0faaab44b4e30a413d7816df5528c6eb057",
        "record_type": "abort_receipt",
        "remote_absent": True,
        "run_id": "a10m5r15r2r1-successor-control-identity-calibration-r0",
        "schema_version": "lemhi-toolkit-record-2",
        "source_commit": "c07a7b6cf50114a8709dedc103105994ae67b6eb",
        "terminal": "LEMHI-TOOLKIT-RUN-ABORTED-BEFORE-SUBMISSION",
    },
    {
        "authority_id": "a10m5r15r2r1-successor-control-identity-calibration-r1-authority",
        "job_local_cleanup": "not_started",
        "package_id": "20260722-a10m5r15r2r1-successor-control-identity-calibration",
        "plan_id": "d25d20a0ff2322bc1d4f4a9a4f82feec02db12f595cad20e0b82f5435d55c47a",
        "producer_version": "lemhi-toolkit-hardening-2",
        "record_sha256": "a42098bd65f69fc4c0a596e17301e679c8498c24f742ef0b532f75dd617c6bf4",
        "record_type": "abort_receipt",
        "remote_absent": True,
        "run_id": "a10m5r15r2r1-successor-control-identity-calibration-r1",
        "schema_version": "lemhi-toolkit-record-2",
        "source_commit": "e93489e2845c65e8ad2946a8efe76da9296b80cc",
        "terminal": "LEMHI-TOOLKIT-RUN-ABORTED-BEFORE-SUBMISSION",
    },
]:
    raise RuntimeError("calibration abort lineage drift")
diagnostics = json.loads(DIAGNOSTICS.read_text(encoding="utf-8"))
if not (
    diagnostics.get("actual_gpu_minutes") == 0
    and diagnostics.get("attempt_count") == 0
    and diagnostics.get("candidate_output_produced") is False
):
    raise RuntimeError("pre-submission diagnostics drift")
if not (
    digest(CORPUS_PIN)
    == "93045d7727a5c0718579ed2222397fb514633f54bec20afd919b61bd6944bc44"
    and digest(CORPUS_VERIFIER)
    == "8ebb71ca9b623cf3626bd5694e580f7d72bd8e565af45dd9b8e150ed769fa11e"
):
    raise RuntimeError("successor corpus verifier publication drift")
parent_failure = contract["parent_failure"]
if parent_failure != failure_projection(failure):
    raise RuntimeError("calibration contract does not bind the complete R2 failure")
for field, expected in EXPECTED_CHAIN.items():
    if parent_failure.get(field) != expected:
        raise RuntimeError(f"calibration contract parent chain drift: {field}")
if not (
    all(contract.get(field) == expected for field, expected in EXPECTED_TOP_LEVEL.items())
    and contract["schema_version"] == 1
    and contract["candidate_output_allowed"] is False
    and contract["maximum_l40_minutes"] == 35
    and contract["control_capacities"] == ["P1", "P2"]
    and contract["control_seeds"] == [147031, 271828, 314159]
    and contract["protected_roles_opened"] == []
    and failure["record_authenticated"] is True
    and failure["record_valid"] is True
    and failure["scientific_interpretation_allowed"] is False
    and failure["control"]["job_receipt_record_sha256"]
    == EXPECTED_CHAIN["job_receipt_record_sha256"]
    and failure["control"]["gate_receipt_sha256"]
    == EXPECTED_CHAIN["gate_receipt_sha256"]
    and failure["matrix_stop"]["record_sha256"]
    == EXPECTED_CHAIN["matrix_stop_record_sha256"]
    and failure["evidence_chain"]["collection_record_sha256"]
    == EXPECTED_CHAIN["collection_record_sha256"]
    and failure["evidence_chain"]["cleanup_record_sha256"]
    == EXPECTED_CHAIN["cleanup_record_sha256"]
    and failure["evidence_chain"]["sanitized_control_stderr_sha256"]
    == EXPECTED_CHAIN["sanitized_control_stderr_sha256"]
    and failure["terminal_record_sha256"]
    == EXPECTED_CHAIN["terminal_record_sha256"]
):
    raise RuntimeError("closed R2 failure chain is incomplete or ambiguous")
if role_map != {
    "candidate_roles": [],
    "control_role": "control-materialization",
    "package_id": contract["package_id"],
    "protected_roles_opened": [],
    "schema_version": 1,
    "submission_waves": [["control-materialization"]],
}:
    raise RuntimeError("control-only role map drift")
for path in sorted(JOBS.glob("*.py")):
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
materializer = (JOBS / "materialize_controls.py").read_text(encoding="utf-8")
builder = (JOBS / "build_control_records.py").read_text(encoding="utf-8")
preparer = (JOBS / "prepare_assets.py").read_text(encoding="utf-8")
admission = (JOBS / "materialize_admission.py").read_text(encoding="utf-8")
required_materializer = (
    '"candidate_output_absent": True',
    "len(summary_rows) == 6",
    '"parent_identity_drift_reproduced"',
    '"static_control_identities_exact"',
)
if any(token not in materializer for token in required_materializer):
    raise RuntimeError("six-row candidate-blind materializer gates incomplete")
identity_contract = contract.get("identity_contract")
if identity_contract != {
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
}:
    raise RuntimeError("control identity gating contract drift")
if not (
    'value["jobs"] = [' in builder
    and 'value["candidate_output_allowed"] = False' in builder
    and '"resource_ceiling_gpu_minutes": 35' in builder
    and 'value["admission_materialization"]["required_roles"] = [CONTROL_ROLE]'
    in builder
    and 'delegated.ROLES = {"control-materialization"}' in admission
    and 'value["admission"]["waves"] = []' in preparer
    and 'value["status"] = "EXECUTION-READY"' in preparer
    and "verify_parent_layout(options.parent_assets, parent)" in preparer
    and "verify_copied_parent(parent, options.output)" in preparer
    and '("cp", "-c", "-p", str(source), str(target))' in preparer
    and "target.stat().st_nlink != 1" in preparer
    and "abort_bundle(options.source_commit)" in builder
    and 'RUN_ID = "a10m5r15r2r1-successor-control-identity-calibration-r2"'
    in preparer
    and 'RUN_ID = "a10m5r15r2r1-successor-control-identity-calibration-r2"'
    in builder
    and 'RUN_ID = "a10m5r15r2r1-successor-control-identity-calibration-r2"'
    in admission
):
    raise RuntimeError("control-only authority/admission projection incomplete")
package_text = (PACKAGE / "package.md").read_text(encoding="utf-8")
if "Status: `SCAFFOLDED`" not in package_text:
    raise RuntimeError("calibration package status drift")
print(
    "A10M5R15R2R1-SCAFFOLD-VERIFIED",
    digest(CONTRACT),
    digest(ROLE_MAP),
)
