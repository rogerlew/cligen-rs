#!/usr/bin/env python3
"""Pin semantic-plan authentication and the exact published R13R2 input."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

package = Path(__file__).resolve().parents[1]
repo = package.parents[2]
path = package / "artifacts/run_temporal_replay.py"
spec = importlib.util.spec_from_file_location("r14_replay", path)
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
semantic = replay.reconstruct_semantic_plan(raw, receipt)
receipt["plan_id"] = hashlib.sha256(replay.canonical(semantic)).hexdigest()
receipt["record_sha256"] = hashlib.sha256(replay.canonical(receipt)).hexdigest()
if replay.authenticate_plan(raw, receipt, source) != semantic:
    raise RuntimeError("semantic plan authentication failed")
tampered = dict(raw)
tampered["evidence_allowlist"] = ["results/other/streams.npz"]
try:
    replay.authenticate_plan(tampered, receipt, source)
except RuntimeError:
    pass
else:
    raise RuntimeError("tampered raw semantic plan was accepted")
try:
    replay.validate_allowlist(["../escape"])
except RuntimeError:
    pass
else:
    raise RuntimeError("unsafe semantic allowlist was accepted")

pin = json.loads((package / "artifacts/replay-predecessor-pin.json").read_text())
r13 = repo / "docs/work-packages/20260720-a10m5r13r2-semantic-plan-replay-authentication-remedy/artifacts/execution"
result_path = r13 / "temporal-result.json"
identity_path = r13 / "replay-identity.json"
identity = json.loads(identity_path.read_text())
result = json.loads(result_path.read_text())
file_id = lambda value: {
    "bytes": value.stat().st_size,
    "sha256": hashlib.sha256(value.read_bytes()).hexdigest(),
}
if (
    pin["campaign_predecessor_commit"] != "4720ea5764fe02c55a3707f94bb6805f5886b812"
    or file_id(result_path) != {
        "bytes": pin["temporal_result"]["bytes"],
        "sha256": pin["temporal_result"]["sha256"],
    }
    or file_id(identity_path) != {
        "bytes": pin["replay_identity"]["bytes"],
        "sha256": pin["replay_identity"]["sha256"],
    }
    or identity["record_sha256"] != pin["replay_identity"]["record_sha256"]
    or result["terminal"] != pin["terminal"]
    or result["eligible_configurations"] != pin["temporal_result"]["eligible_configurations"]
    or result["protected_roles_opened"] != []
):
    raise RuntimeError("published R13R2 replay/result input identity drift")
print("A10M5R14-REPLAY-AUTHENTICATION-TEST-PASS")
