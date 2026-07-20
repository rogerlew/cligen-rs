#!/usr/bin/env python3
"""Exercise R13R1 builder identities and exact R13 abort inheritance."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import types
from pathlib import Path

path = Path(__file__).parent / "jobs/build_control_records.py"
spec = importlib.util.spec_from_file_location("r13r1_builder", path)
assert spec and spec.loader
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

source = path.read_text(encoding="utf-8")
if source.index("verify_transitive_builder(_head)") > source.index(
    "spec.loader.exec_module(builder)"
):
    raise RuntimeError("R12R1 builder is imported transitively before authentication")

predecessor = builder.predecessor_bundle()
if (
    predecessor["record_commit"] != builder.PARENT_COMMIT
    or predecessor["package_id"]
    != "20260720-a10m5r13-selector-aligned-continuous-hierarchy"
):
    raise RuntimeError("exact R13 abort predecessor bundle drift")

with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    transitive = root / "r12r1-builder.py"
    transitive.write_bytes(b"published-r12r1-builder")
    builder.verify_transitive_builder(
        "unused", source=transitive, published=b"published-r12r1-builder"
    )
    transitive.write_bytes(b"drift")
    try:
        builder.verify_transitive_builder(
            "unused", source=transitive, published=b"published-r12r1-builder"
        )
    except RuntimeError:
        pass
    else:
        raise RuntimeError("transitive R12R1 builder drift was accepted")

    authority_path, plan_path = root / "authority.json", root / "plan.json"

    def fake_authority(options) -> None:
        options.output.write_text(json.dumps({
            "package_id": builder.PACKAGE_ID,
            "resource_ceiling_gpu_minutes": 515,
            "run_id": builder.RUN_ID,
        }), encoding="utf-8")

    builder.base_authority = fake_authority
    builder.authority(types.SimpleNamespace(output=authority_path))

    allowlist = [f"evidence/{index}" for index in range(20)]

    def fake_plan(options) -> None:
        options.output.write_text(json.dumps({
            "admission_materialization": {"record_type": builder.RECORD_TYPE},
            "evidence_allowlist": allowlist,
            "evidence_volume": {
                "maximum_expanded_bytes": 128000000,
                "maximum_file_bytes": 64000000,
                "maximum_files": len(allowlist),
            },
            "package_id": builder.PACKAGE_ID,
            "run_id": builder.RUN_ID,
            "submission_waves": [
                ["control-materialization"],
                [builder.ROLES[0][0], builder.ROLES[1][0]],
            ],
        }), encoding="utf-8")

    builder.base_plan = fake_plan
    builder.plan(types.SimpleNamespace(output=plan_path))

if not (
    builder.delegated.PACKAGE_ID == builder.PACKAGE_ID
    and builder.delegated.RUN_ID == builder.RUN_ID
    and builder.delegated.AUTHORITY_ID == f"{builder.RUN_ID}-authority"
    and builder.delegated.BUDGET_ID == f"{builder.RUN_ID}-budget"
):
    raise RuntimeError("fresh R13R1 authority/budget identity drift")
print("A10M5R13R1-BUILDER-TEST-PASS")
