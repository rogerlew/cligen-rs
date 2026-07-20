#!/usr/bin/env python3
"""Exercise R14 parent provenance and fresh R14R1 receipt authentication."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

path = Path(__file__).parent / "jobs/materialize_admission.py"
spec = importlib.util.spec_from_file_location("r14r1_materialize", path)
assert spec and spec.loader
wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper)

with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    parent = root / "parent.py"
    parent.write_bytes(b"published-r14-materializer")
    wrapper.verify_parent_wrapper(
        source=parent, published=b"published-r14-materializer"
    )
    parent.write_bytes(b"drift")
    try:
        wrapper.verify_parent_wrapper(
            source=parent, published=b"published-r14-materializer"
        )
    except RuntimeError:
        pass
    else:
        raise RuntimeError("unpublished R14 materializer drift was accepted")

    target = root / "admission.json"
    role = "control-materialization"
    state_sha256, source_commit = "1" * 64, "2" * 40
    receipt = {
        "attempt_index": 0,
        "authority_id": f"{wrapper.RUN_ID}-authority",
        "decision": "PASS",
        "gates": {"admitted": True},
        "input_identities": {"toolkit_state_sha256": state_sha256},
        "package_id": wrapper.PACKAGE_ID,
        "record_type": wrapper.RECORD_TYPE,
        "role": role,
        "run_id": wrapper.RUN_ID,
        "schema_version": "lemhi-toolkit-record-2",
        "source_commit": source_commit,
        "valid": True,
    }

    def sign() -> None:
        receipt.pop("record_sha256", None)
        payload = json.dumps(receipt, separators=(",", ":"), sort_keys=True).encode()
        receipt["record_sha256"] = hashlib.sha256(payload).hexdigest()

    def stage(_arguments: list[str], *, input_bytes: bytes | None = None) -> None:
        del input_bytes
        target.write_text(json.dumps(receipt), encoding="utf-8")

    wrapper.delegated.run = stage
    sign()
    accepted = wrapper.fetch_and_verify(
        target,
        role=role,
        state_sha256=state_sha256,
        source_commit=source_commit,
    )
    if accepted["record_type"] != wrapper.RECORD_TYPE:
        raise RuntimeError("fresh R14R1 receipt was not accepted")
    for forbidden in (
        "a10m5r14-submission-admission",
        "a10m5r13r1-submission-admission",
    ):
        receipt["record_type"] = forbidden
        sign()
        try:
            wrapper.fetch_and_verify(
                target,
                role=role,
                state_sha256=state_sha256,
                source_commit=source_commit,
            )
        except RuntimeError:
            pass
        else:
            raise RuntimeError(f"inherited receipt type was accepted: {forbidden}")

print("A10M5R14R1-MATERIALIZE-WRAPPER-TEST-PASS")
