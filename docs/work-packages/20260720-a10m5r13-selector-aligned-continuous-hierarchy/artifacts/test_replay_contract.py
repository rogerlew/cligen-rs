#!/usr/bin/env python3
"""Static fail-closed checks for the pre-cleanup replay command contract."""

from pathlib import Path

source = (Path(__file__).parent / "run_temporal_replay.py").read_text(encoding="utf-8")
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
print("A10M5R13-REPLAY-CONTRACT-TEST-PASS")
