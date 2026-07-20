#!/usr/bin/env python3
"""Exercise inherited-source and R13 receipt authentication behavior."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

path = Path(__file__).parent / "jobs" / "materialize_admission.py"
spec = importlib.util.spec_from_file_location("r13_admission", path)
assert spec and spec.loader
wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper)

with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    delegated = root / "delegated.py"
    delegated.write_bytes(b"reviewed")
    wrapper.verify_inherited_source("unused", source=delegated, published=b"reviewed")
    delegated.write_bytes(b"drift")
    try:
        wrapper.verify_inherited_source("unused", source=delegated, published=b"reviewed")
    except RuntimeError:
        pass
    else:
        raise RuntimeError("inherited admission source drift was accepted")

    target = root / "admission.json"
    state_sha256 = "1" * 64
    source_commit = "2" * 40
    receipt = {
        "attempt_index": 0,
        "authority_id": "authority",
        "decision": "PASS",
        "gates": {"admitted": True},
        "input_identities": {"toolkit_state_sha256": state_sha256},
        "package_id": wrapper.PACKAGE_ID,
        "record_type": "a10m5r13-submission-admission",
        "role": "control-materialization",
        "run_id": wrapper.RUN_ID,
        "schema_version": "lemhi-toolkit-record-2",
        "source_commit": source_commit,
        "valid": True,
    }

    def canonical(value: dict) -> bytes:
        return json.dumps(value, separators=(",", ":"), sort_keys=True).encode()

    receipt["record_sha256"] = hashlib.sha256(canonical(receipt)).hexdigest()

    def stage(_arguments: list[str], *, input_bytes: bytes | None = None) -> None:
        del input_bytes
        target.write_text(json.dumps(receipt), encoding="utf-8")

    wrapper.inherited.run = stage
    accepted = wrapper.fetch_and_verify(
        target,
        role="control-materialization",
        state_sha256=state_sha256,
        source_commit=source_commit,
    )
    if accepted["record_type"] != "a10m5r13-submission-admission":
        raise RuntimeError("authenticated R13 admission was not accepted")
    receipt["record_type"] = "a10m5r12-submission-admission"
    receipt.pop("record_sha256")
    receipt["record_sha256"] = hashlib.sha256(canonical(receipt)).hexdigest()
    try:
        wrapper.fetch_and_verify(
            target,
            role="control-materialization",
            state_sha256=state_sha256,
            source_commit=source_commit,
        )
    except RuntimeError:
        pass
    else:
        raise RuntimeError("R12 admission record type was accepted for R13")

print("A10M5R13-ADMISSION-WRAPPER-TEST-PASS")
