#!/usr/bin/env python3
"""Use the corrected A10M5R8 builder with R3 package identities."""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SOURCE = REPO / "docs/work-packages/20260719-a10m5r8-climate-statistics-objective/artifacts/jobs/build_control_records.py"
SPEC = importlib.util.spec_from_file_location("a10m5r8_control_records", SOURCE)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("A10M5R8 control-record builder cannot be loaded")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
MODULE.PACKAGE_ID = "20260719-a10m5r8r3-calendar-end-exclusion-remedy"
MODULE.RUN_ID = "a10m5r8r3-climate-objective-r0"
MODULE.AUTHORITY_ID = "a10m5r8r3-climate-objective-authority"
MODULE.BUDGET_ID = "a10m5r8r3-climate-objective-budget"
MODULE.AUTHORITY_TOKEN = "a10m5r8r3-climate-objective-authority-token"

if __name__ == "__main__":
    MODULE.main()
