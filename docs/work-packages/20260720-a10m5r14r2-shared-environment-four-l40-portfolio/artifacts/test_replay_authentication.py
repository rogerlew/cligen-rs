#!/usr/bin/env python3
"""Exercise R14R2 semantic-plan and child-record authentication helpers."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

path = Path(__file__).resolve().parent / "run_temporal_replay.py"
spec = importlib.util.spec_from_file_location("r14r2_replay", path)
assert spec and spec.loader
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)

source = "a" * 40
raw = {
    "created_at": "not-semantic",
    "evidence_allowlist": ["results/arm/streams.npz"],
    "package_id": replay.PACKAGE_ID,
    "run_id": replay.RUN_ID,
    "source_commit": source,
}
receipt = {
    "cluster_profile_sha256": "b" * 64,
    "package_id": replay.PACKAGE_ID,
    "provider_stack": [{"provider_id": "transport"}],
    "record_type": "run_plan_receipt",
    "run_id": replay.RUN_ID,
    "source_commit": source,
}
semantic = replay.parent.reconstruct_semantic_plan(raw, receipt)
receipt["plan_id"] = hashlib.sha256(replay.parent.canonical(semantic)).hexdigest()
receipt["record_sha256"] = hashlib.sha256(replay.parent.canonical(receipt)).hexdigest()
assert replay.parent.authenticate_plan(raw, receipt, source) == semantic

record = {"protected_roles_opened": [], "role": "arm", "valid": True}
record["record_sha256"] = hashlib.sha256(replay.simple_canonical(record)).hexdigest()
assert replay.simple_authenticated(record)
record["role"] = "tampered"
assert not replay.simple_authenticated(record)

assert replay.PACKAGE_ID not in replay.PARENT.read_text()
assert replay.RUN_ID not in replay.PARENT.read_text()
print("A10M5R14R2-REPLAY-AUTHENTICATION-PASS")
