#!/usr/bin/env python3
"""Freeze A7a sources and parent evidence before new derived output."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PACKAGE = Path(__file__).resolve().parent
OUTPUT = PACKAGE / "pre-analysis-freeze-v4.json"
PRIOR_FREEZE = PACKAGE / "pre-analysis-freeze-v3.json"
AMENDMENT = PACKAGE / "analysis-amendment-003.md"
SOURCE_COMMIT = "d27a008e91a4853044aed5207d02a3aeb631ac8c"
ANALYSIS_OUTPUTS = (
    "a7a-analysis-v1.json",
    "a7a-decision-v1.json",
    "findings.md",
)
FROZEN_SOURCES = (
    "design.md",
    "measurement-contract-v1.json",
    "claim-evidence-ledger.md",
    "pre-analysis-amendment-001.md",
    "pre-analysis-amendment-002.md",
    "analysis-amendment-003.md",
    "analyze-a7a.py",
    "verify-a7a.py",
    "freeze-a7a.py",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if head != SOURCE_COMMIT:
        raise ValueError(f"source commit {head} != {SOURCE_COMMIT}")
    for name in ANALYSIS_OUTPUTS:
        if (PACKAGE / name).exists():
            raise ValueError(f"A7a outcome exists before freeze: {name}")
    contract = json.loads((PACKAGE / "measurement-contract-v1.json").read_text())
    parents = {}
    for name, record in contract["inputs"].items():
        path = ROOT / record["path"]
        digest = sha256(path)
        if digest != record["sha256"]:
            raise ValueError(f"parent evidence changed: {name}")
        parents[name] = {
            "path": record["path"],
            "sha256": digest,
        }
    sources = {
        name: sha256(PACKAGE / name)
        for name in FROZEN_SOURCES
    }
    value = {
        "amendment": {
            "path": AMENDMENT.name,
            "sha256": sha256(AMENDMENT),
        },
        "amends_freeze": {
            "path": PRIOR_FREEZE.name,
            "sha256": sha256(PRIOR_FREEZE),
        },
        "access_boundary": (
            "Frozen before any A7a seasonal aggregation, higher-order occurrence "
            "residual, trajectory-null comparison, gap ranking, propagation "
            "diagnostic, or terminal decision was produced; parent A5a evidence "
            "was already exposed."
        ),
        "freeze_schema_version": 4,
        "frozen_sources": sources,
        "parent_inputs": parents,
        "source_commit": SOURCE_COMMIT,
    }
    OUTPUT.write_text(
        json.dumps(value, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
