#!/usr/bin/env python3
"""Verify the zero-allocation R2R1R1 scoring freeze."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
REPO = PACKAGE.parents[2]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_identity(root: Path) -> tuple[int, int, str]:
    value = hashlib.sha256()
    files = 0
    byte_count = 0
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        payload = path.read_bytes()
        relative = str(path.relative_to(root))
        value.update(relative.encode() + b"\0" + str(len(payload)).encode() + b"\0" + hashlib.sha256(payload).hexdigest().encode() + b"\n")
        files += 1
        byte_count += len(payload)
    return files, byte_count, value.hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument("--scratch", type=Path, required=True)
parser.add_argument("--collection", type=Path, required=True)
parser.add_argument("--terminal", type=Path, required=True)
parser.add_argument("--parent-output", type=Path, required=True)
options = parser.parse_args()
assert tree_identity(options.scratch) == (354, 280551300, "c4d7bf9c2b8441b89ceda42ec1ef5e7976ee533f998eff473bece2f967154607")
assert digest(options.collection) == "57ebbb055620697d8db424ccf32214c430a62bd2f33a8362fd41b542d0af0616"
assert digest(options.terminal) == "e9827a06d4691430c2cd32eeb728e2aa4be109675cc84b54d21211a3a8005c3b"
assert not options.parent_output.exists()
parent = REPO / "docs/work-packages/20260718-a10m5r4r2r1-reconstruction-identity-remedy/package.md"
assert "EXECUTED-HOLD-EVALUATION-YEAR-AXIS" in parent.read_text(encoding="utf-8")
source = (PACKAGE / "artifacts/jobs/score.py").read_text(encoding="utf-8")
assert "2400 + 8 * position + (0 if leap else 1)" in source
compile(source, "score.py", "exec")
print("A10M5R4R2R1R1-FREEZE-READY")
