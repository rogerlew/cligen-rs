#!/usr/bin/env python3
"""Exercise R13-controller provenance and R13R1 receipt authentication."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

path = Path(__file__).parent / "jobs/materialize_admission.py"
spec = importlib.util.spec_from_file_location("r13r1_admission", path)
assert spec and spec.loader
wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper)

with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    controller = root / "controller.py"
    controller.write_bytes(b"published-r13-controller")
    wrapper.verify_inherited_controller(
        "unused", source=controller, published=b"published-r13-controller"
    )
    controller.write_bytes(b"drift")
    try:
        wrapper.verify_inherited_controller(
            "unused", source=controller, published=b"published-r13-controller"
        )
    except RuntimeError:
        pass
    else:
        raise RuntimeError("inherited R13 controller drift was accepted")

    target = root / "admission.json"
    state_sha256, source_commit = "1" * 64, "2" * 40
    receipt = {
        "attempt_index": 0,
        "authority_id": "r13r1-authority",
        "decision": "PASS",
        "gates": {"admitted": True},
        "input_identities": {"toolkit_state_sha256": state_sha256},
        "package_id": wrapper.PACKAGE_ID,
        "record_type": wrapper.RECORD_TYPE,
        "role": "control-materialization",
        "run_id": wrapper.RUN_ID,
        "schema_version": "lemhi-toolkit-record-2",
        "source_commit": source_commit,
        "valid": True,
    }

    def canonical(value: dict) -> bytes:
        return json.dumps(value, separators=(",", ":"), sort_keys=True).encode()

    def sign() -> None:
        receipt.pop("record_sha256", None)
        receipt["record_sha256"] = hashlib.sha256(canonical(receipt)).hexdigest()

    def stage(_arguments: list[str], *, input_bytes: bytes | None = None) -> None:
        del input_bytes
        target.write_text(json.dumps(receipt), encoding="utf-8")

    wrapper.delegated.run = stage
    sign()
    accepted = wrapper.fetch_and_verify(
        target, role="control-materialization",
        state_sha256=state_sha256, source_commit=source_commit,
    )
    if accepted["record_type"] != wrapper.RECORD_TYPE:
        raise RuntimeError("authenticated R13R1 admission was not accepted")
    for forbidden in (
        "a10m5r13-submission-admission", "a10m5r12-submission-admission"
    ):
        receipt["record_type"] = forbidden
        sign()
        try:
            wrapper.fetch_and_verify(
                target, role="control-materialization",
                state_sha256=state_sha256, source_commit=source_commit,
            )
        except RuntimeError:
            pass
        else:
            raise RuntimeError(f"inherited receipt type was accepted: {forbidden}")

print("A10M5R13R1-ADMISSION-WRAPPER-TEST-PASS")
