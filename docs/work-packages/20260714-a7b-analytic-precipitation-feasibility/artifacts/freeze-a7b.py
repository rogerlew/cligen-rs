#!/usr/bin/env python3
"""Freeze A7b methods and identities before the first authoritative run."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ARTIFACTS = Path(__file__).resolve().parent
PACKAGE = ARTIFACTS.parent
REPO = PACKAGE.parents[2]
OUTPUT_NAMES = (
    "a7b-analysis-v1.json",
    "a7b-decision-v1.json",
    "findings.md",
)
FROZEN_PATHS = (
    "docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/artifacts/design.md",
    "docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/artifacts/feasibility-contract-v1.json",
    "docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/artifacts/analyze-a7b.py",
    "docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/artifacts/verify-a7b.py",
    "docs/work-packages/20260714-a7b-analytic-precipitation-feasibility/artifacts/freeze-a7b.py",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(path)
    return value


def main() -> None:
    output = ARTIFACTS / "pre-analysis-freeze-v1.json"
    if output.exists() or any((ARTIFACTS / name).exists() for name in OUTPUT_NAMES):
        raise SystemExit("refusing to freeze after a freeze or A7b outcome exists")
    contract = load_json(ARTIFACTS / "feasibility-contract-v1.json")
    if (
        subprocess.run(
            ["git", "diff", "--quiet", contract["source_commit"], "--", "crates"],
            cwd=REPO,
            check=False,
        ).returncode
        != 0
    ):
        raise SystemExit("production crates differ from the frozen source commit")
    for entry in contract["inputs"].values():
        path = REPO / entry["path"]
        if sha256(path.read_bytes()) != entry["sha256"]:
            raise SystemExit(f"input mismatch: {entry['path']}")
    frozen = {relative: sha256((REPO / relative).read_bytes()) for relative in FROZEN_PATHS}
    value = {
        "freeze_id": "a7b_pre_analysis_freeze_v1",
        "freeze_status": "FROZEN-BEFORE-A7B-OUTCOME",
        "frozen_files_sha256": frozen,
        "input_files_sha256": {
            entry["path"]: entry["sha256"] for entry in contract["inputs"].values()
        },
        "method_boundary": (
            "Any change to a frozen file after this record invalidates A7b output; "
            "outcome-time threshold changes are prohibited."
        ),
        "schema_version": 1,
        "source_commit": contract["source_commit"],
    }
    output.write_bytes(canonical_json_bytes(value))
    print(sha256(output.read_bytes()))


if __name__ == "__main__":
    main()
