#!/usr/bin/env python3
"""Verify the A10M5O2D1 source and authority freeze."""

from __future__ import annotations

import ast
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
JOBS = PACKAGE / "artifacts/jobs"

for name in ("interconnect.py", "merge_results.py", "prepare_assets.py", "build_control_records.py"):
    ast.parse((JOBS / name).read_text(encoding="utf-8"), filename=name)
for name in ("run-diagnostic.sh", "job-common.sh"):
    source = (JOBS / name).read_text(encoding="utf-8")
    if not source.startswith("#!/bin/sh\nset -eu\n"):
        raise SystemExit(f"unsafe shell prefix: {name}")
builder = (JOBS / "build_control_records.py").read_text(encoding="utf-8")
for fragment in (
    '"resource_ceiling_gpu_minutes": 45',
    '"gpus": 4',
    '"gres": "gpu:l40:4"',
    '"time_limit_minutes": 10',
    '"predecessor_evidence": []',
    "accelerator-l40-multigpu-v1.json",
):
    if fragment not in builder:
        raise SystemExit(f"control freeze drift: {fragment}")
benchmark = (JOBS / "interconnect.py").read_text(encoding="utf-8")
for fragment in ("1 << 20", "16 << 20", "128 << 20", "can_device_access_peer"):
    if fragment not in benchmark:
        raise SystemExit(f"benchmark freeze drift: {fragment}")
runner = (JOBS / "run-diagnostic.sh").read_text(encoding="utf-8")
for fragment in ("nvidia-smi topo -m", "nvidia-smi topo -p2p r", "NCCL_P2P_DISABLE=1"):
    if fragment not in runner:
        raise SystemExit(f"runner freeze drift: {fragment}")
print("A10M5O2D1_FREEZE_PASS")
