#!/usr/bin/env python3
"""Exercise the R13 authority/plan post-processing without private caches."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import types
from pathlib import Path

path = Path(__file__).parent / "jobs" / "build_control_records.py"
spec = importlib.util.spec_from_file_location("r13_builder", path)
assert spec and spec.loader
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    authority_path = root / "authority.json"
    plan_path = root / "plan.json"

    def fake_authority(options) -> None:
        builder.inherited.write(options.output, {
            "package_id": builder.PACKAGE_ID,
            "resource_ceiling_gpu_minutes": 395,
        })

    builder.base_authority = fake_authority
    builder.authority(types.SimpleNamespace(output=authority_path))
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    if authority["resource_ceiling_gpu_minutes"] != 515:
        raise RuntimeError("R13 authority ceiling rewrite failed")

    def fake_plan(options) -> None:
        builder.inherited.write(options.output, {
            "admission_materialization": {
                "record_type": "old",
                "required_before_each_submit": True,
                "required_roles": ["control-materialization", *(row[0] for row in builder.ROLES)],
            },
            "evidence_allowlist": [f"evidence/{index}" for index in range(20)],
            "jobs": [
                {"role": "control-materialization", "time_limit_minutes": 30},
                *( {"role": row[0], "time_limit_minutes": 180} for row in builder.ROLES ),
            ],
        })

    builder.base_plan = fake_plan
    builder.plan(types.SimpleNamespace(output=plan_path))
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan["admission_materialization"]["record_type"] != builder.RECORD_TYPE:
        raise RuntimeError("R13 admission type rewrite failed")
    if [job["time_limit_minutes"] for job in plan["jobs"]] != [30, 240, 240]:
        raise RuntimeError("R13 plan time limits drift")
    if plan["submission_waves"] != [["control-materialization"], [row[0] for row in builder.ROLES]]:
        raise RuntimeError("candidate concurrency wave drift")
    volume = plan["evidence_volume"]
    if volume != {"maximum_expanded_bytes": 128000000, "maximum_file_bytes": 64000000, "maximum_files": 20}:
        raise RuntimeError("toolkit evidence volume contract drift")

print("A10M5R13-BUILDER-TEST-PASS")
