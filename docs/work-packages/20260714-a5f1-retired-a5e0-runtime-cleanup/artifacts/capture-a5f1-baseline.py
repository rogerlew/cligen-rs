#!/usr/bin/env python3
"""Capture A5f1 pre-removal source and preserved-record identities."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


SOURCE_COMMIT = "9eada9229606667ff083f69fe968364dead31d10"

REMOVED = (
    "crates/cligen/src/a5e0.rs",
    "crates/cligen/examples/a5e0_runner.rs",
)

TOUCHED = (
    "crates/cligen/src/lib.rs",
    "crates/cligen/src/modes.rs",
    "crates/cligen/src/rng.rs",
)

PRESERVED = (
    "docs/specifications/SPEC-A5E0-PILOT.md",
    "docs/specifications/a5e0-campaign-evidence-v1.schema.json",
    "docs/specifications/a5e0-coefficients-v1.schema.json",
    "docs/reports/a5e0-direct-annual-state-pilot-report.md",
    "docs/reports/a5e0-direct-annual-state-pilot-report.manifest.json",
    "docs/work-packages/20260714-a5e0-direct-annual-state-pilot/package.md",
    "docs/work-packages/20260714-a5f0-annual-state-failure-attribution/package.md",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    if not path.is_file():
        raise ValueError(f"missing baseline input: {relative}")
    return {"bytes": path.stat().st_size, "path": relative, "sha256": sha256(path)}


def main() -> int:
    root = repo_root()
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if head != SOURCE_COMMIT:
        raise ValueError(f"expected clean source commit {SOURCE_COMMIT}, found {head}")
    changed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if changed:
        raise ValueError("tracked worktree differs from the A5f1 source commit")
    value = {
        "baseline_schema": "a5f1_baseline_v1",
        "historical_implementation_commit": "1ca40bbe006ed5d823d2dd8e373f720f20d60ba0",
        "preserved_records": [artifact(root, path) for path in PRESERVED],
        "removed_files": [artifact(root, path) for path in REMOVED],
        "source_commit": SOURCE_COMMIT,
        "touched_files": [artifact(root, path) for path in TOUCHED],
    }
    output = Path(__file__).with_name("a5f1-baseline-v1.json")
    output.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n",
        encoding="utf-8",
    )
    print(output.relative_to(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
