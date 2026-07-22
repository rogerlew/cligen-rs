#!/usr/bin/env python3
"""Verify the successor control-calibration scaffold fails closed."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent.parent
REPO = PACKAGE.parents[2]
R2 = PACKAGE.parent / "20260721-a10m5r15r2-external-normal-conditioning-execution"
CONTRACT = PACKAGE / "artifacts/control-calibration-contract.json"
ROLE_MAP = PACKAGE / "artifacts/control-role-map.json"
FAILURE = R2 / "artifacts/execution-r0-failure.json"
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


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
failure = json.loads(FAILURE.read_text(encoding="utf-8"))
role_map = json.loads(ROLE_MAP.read_text(encoding="utf-8"))
parent_failure = contract["parent_failure"]
for field, expected in EXPECTED_CHAIN.items():
    if parent_failure.get(field) != expected:
        raise RuntimeError(f"calibration contract parent chain drift: {field}")
if not (
    contract["candidate_output_allowed"] is False
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
if not (
    'value["jobs"] = [' in builder
    and 'value["candidate_output_allowed"] = False' in builder
    and '"resource_ceiling_gpu_minutes": 35' in builder
    and 'value["admission_materialization"]["required_roles"] = [CONTROL_ROLE]'
    in builder
    and 'delegated.ROLES = {"control-materialization"}' in admission
    and 'value["admission"]["waves"] = []' in preparer
    and 'value["status"] = "EXECUTION-READY"' in preparer
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
