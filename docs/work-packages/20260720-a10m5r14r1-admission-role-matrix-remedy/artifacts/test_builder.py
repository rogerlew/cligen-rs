#!/usr/bin/env python3
"""Exercise fresh R14R1 authority, plan, abort, and source identities."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import types
from pathlib import Path

path = Path(__file__).parent / "jobs/build_control_records.py"
spec = importlib.util.spec_from_file_location("r14r1_builder", path)
assert spec and spec.loader
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

abort = builder.abort_bundle()
if (
    abort["parent_receipt_source_commit"] != builder.PARENT_COMMIT
    or abort["record_sha256"]
    != "65dfe82ad1b149fdb0dbf1b10555d574286b2f6d2e6a31c6cfbb17412acd29ac"
):
    raise RuntimeError("R14 abort bundle drift")

with tempfile.TemporaryDirectory() as scratch:
    root = Path(scratch)
    parent_source = root / "parent.py"
    parent_source.write_bytes(b"published-r14-builder")
    builder.verify_parent_builder(
        source=parent_source, published=b"published-r14-builder"
    )
    parent_source.write_bytes(b"drift")
    try:
        builder.verify_parent_builder(
            source=parent_source, published=b"published-r14-builder"
        )
    except RuntimeError:
        pass
    else:
        raise RuntimeError("unpublished R14 builder drift was accepted")

    authority_path, plan_path = root / "authority.json", root / "plan.json"

    def fake_authority(options) -> None:
        options.output.write_text(
            json.dumps({"package_id": builder.PACKAGE_ID}), encoding="utf-8"
        )

    builder.base_authority = fake_authority
    builder.authority(types.SimpleNamespace(output=authority_path))
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    if authority["predecessor_package_evidence"] != abort:
        raise RuntimeError("fresh authority lacks exact R14 abort")

    expected_roles = ["control-materialization", *(row[0] for row in builder.ROLES)]

    def fake_plan(options) -> None:
        options.output.write_text(
            json.dumps(
                {
                    "admission_materialization": {},
                    "jobs": [{"role": role} for role in expected_roles],
                }
            ),
            encoding="utf-8",
        )

    builder.base_plan = fake_plan
    builder.plan(types.SimpleNamespace(output=plan_path))
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if (
        plan["admission_materialization"]["record_type"] != builder.RECORD_TYPE
        or plan["admission_materialization"]["required_roles"] != expected_roles
        or plan["submission_waves"] != [
            ["control-materialization"],
            expected_roles[1:],
        ]
        or plan["predecessor_package_evidence"] != abort
    ):
        raise RuntimeError("fresh R14R1 plan identity/wave drift")

if not (
    builder.delegated.PACKAGE_ID == builder.PACKAGE_ID
    and builder.delegated.RUN_ID == builder.RUN_ID
    and builder.delegated.AUTHORITY_ID == f"{builder.RUN_ID}-authority"
    and builder.delegated.BUDGET_ID == f"{builder.RUN_ID}-budget"
):
    raise RuntimeError("fresh R14R1 authority/budget identity drift")
print("A10M5R14R1-BUILDER-TEST-PASS")
