#!/usr/bin/env python3
"""Fail-closed checks for the pre-cleanup replay command contract."""

import hashlib
import importlib.util
import tempfile
from pathlib import Path

replay_path = Path(__file__).parent / "run_temporal_replay.py"
source = replay_path.read_text(encoding="utf-8")
required = (
    '"--neural-root", str(options.evidence_root)',
    'collection.get("remote_cleanup_performed") is not True',
    'collection.get("plan_id") == plan.get("plan_id")',
    'runtime != {"numpy": "2.2.6", "python": "3.10.14"}',
    'corpus != manifest["assets"]["corpus.tar"]',
    'data_root != predecessor["data_root_tree"]',
    'result.get("prism_provenance") != predecessor["prism_provenance"]',
    'if results[0].read_bytes() != results[1].read_bytes()',
    'result.get("protected_roles_opened") != []',
)
if any(value not in source for value in required):
    raise RuntimeError("pre-cleanup replay contract is incomplete")
if 'str(options.evidence_root / "results")' in source:
    raise RuntimeError("selector neural root would double-nest results")

spec = importlib.util.spec_from_file_location("r13r1_replay", replay_path)
assert spec and spec.loader
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)
with tempfile.TemporaryDirectory() as scratch:
    asset = Path(scratch) / "selector.py"
    asset.write_bytes(b"selector bytes")
    entry = {
        "bytes": asset.stat().st_size,
        "sha256": hashlib.sha256(asset.read_bytes()).hexdigest(),
        "source_path": "artifacts/jobs/selector.py",
    }
    if replay.selector_asset_identity(asset, entry, asset.name) != {
        "bytes": entry["bytes"], "sha256": entry["sha256"]
    }:
        raise RuntimeError("selector identity did not ignore source_path metadata")
    entry["sha256"] = "0" * 64
    try:
        replay.selector_asset_identity(asset, entry, asset.name)
    except RuntimeError:
        pass
    else:
        raise RuntimeError("selector byte drift was accepted")

print("A10M5R13R1-REPLAY-CONTRACT-TEST-PASS")
