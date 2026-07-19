#!/usr/bin/env python3
"""Verify the century-safe zero-allocation scoring correction."""

from __future__ import annotations

import argparse
import calendar
import hashlib
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]

parser = argparse.ArgumentParser()
parser.add_argument("--scratch", type=Path, required=True)
parser.add_argument("--parent-output", type=Path, required=True)
options = parser.parse_args()
value = hashlib.sha256(); files = 0; byte_count = 0
for path in sorted(item for item in options.scratch.rglob("*") if item.is_file()):
    payload = path.read_bytes(); relative = str(path.relative_to(options.scratch))
    value.update(relative.encode() + b"\0" + str(len(payload)).encode() + b"\0" + hashlib.sha256(payload).hexdigest().encode() + b"\n")
    files += 1; byte_count += len(payload)
assert (files, byte_count, value.hexdigest()) == (354, 280551300, "c4d7bf9c2b8441b89ceda42ec1ef5e7976ee533f998eff473bece2f967154607")
assert not options.parent_output.exists()
for position in range(30):
    leap = 2000 + 16 * position
    assert calendar.isleap(leap)
    assert not calendar.isleap(leap + 1)
    assert 1 < (2000 + 16 * (position + 1) if position < 29 else 3000) - (leap + 1)
r1 = REPO / "docs/work-packages/20260718-a10m5r4r2r1r1-evaluation-year-axis-remedy/package.md"
assert "EXECUTED-HOLD-LEAP-CENTURY" in r1.read_text(encoding="utf-8")
source = (PACKAGE / "artifacts/jobs/score.py").read_text(encoding="utf-8")
assert "2000 + 16 * position + (0 if leap else 1)" in source
compile(source, "score.py", "exec")
print("A10M5R4R2R1R2-FREEZE-READY")
