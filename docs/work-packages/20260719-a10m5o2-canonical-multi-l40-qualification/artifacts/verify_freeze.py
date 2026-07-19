#!/usr/bin/env python3
"""Verify the A10M5O2 source and authority freeze before live execution."""

from __future__ import annotations

import ast
import json
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[2]
JOBS = PACKAGE / "artifacts/jobs"


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise SystemExit(detail)


for name in ("qualify.py", "rank_failure.py", "prepare_assets.py", "build_control_records.py"):
    ast.parse((JOBS / name).read_text(encoding="utf-8"), filename=name)
for name in ("run-qualification.sh", "job-common.sh"):
    source = (JOBS / name).read_text(encoding="utf-8")
    require(source.startswith("#!/bin/sh\nset -eu\n"), f"unsafe shell prefix: {name}")

builder = (JOBS / "build_control_records.py").read_text(encoding="utf-8")
for fragment in (
    '"resource_ceiling_gpu_minutes": 90',
    '"predecessor_evidence": []',
    '("single-baseline", 1, 8',
    '("dual-qualification", 2, 10',
    '("quad-qualification", 4, 12',
    '("dual-rank-failure", 2, 3',
    "accelerator-l40-multigpu-v1.json",
):
    require(fragment in builder, f"control freeze drift: {fragment}")

provider = json.loads(
    (ROOT / "research/a10/lemhi_toolkit/providers/accelerator-l40-multigpu-v1.json").read_text(encoding="utf-8")
)
require(provider["provides"]["accelerator_maximum_devices"] == 4, "provider maximum")
package = (PACKAGE / "package.md").read_text(encoding="utf-8")
for excluded in ("cross-node", "A10M6", "heterogeneous"):
    require(excluded in package, f"missing exclusion: {excluded}")
print("A10M5O2_FREEZE_PASS")
