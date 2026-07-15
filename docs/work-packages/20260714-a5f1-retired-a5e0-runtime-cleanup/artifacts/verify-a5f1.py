#!/usr/bin/env python3
"""Verify A5f1 runtime removal and historical-record preservation."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


PRE_A5E0_COMMIT = "27e5e7754bdfafcca649a71d0f5576910433d0d3"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(root: Path, *command: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )


def main() -> int:
    root = repo_root()
    artifacts = root / (
        "docs/work-packages/20260714-a5f1-retired-a5e0-runtime-cleanup/artifacts"
    )
    baseline = load_json(artifacts / "a5f1-baseline-v1.json")

    for record in baseline["removed_files"]:
        if (root / record["path"]).exists():
            raise ValueError(f"retired runtime still exists: {record['path']}")

    for record in baseline["preserved_records"]:
        path = root / record["path"]
        if not path.is_file():
            raise ValueError(f"preserved record is missing: {record['path']}")
        if path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
            raise ValueError(f"preserved record changed: {record['path']}")

    implementation = baseline["historical_implementation_commit"]
    if run(root, "git", "cat-file", "-e", f"{implementation}^{{commit}}").returncode != 0:
        raise ValueError("historical A5e0 implementation commit is unreachable")

    restored_paths = [record["path"] for record in baseline["touched_files"]]
    restored_paths.extend(record["path"] for record in baseline["removed_files"])
    comparison = run(root, "git", "diff", "--quiet", PRE_A5E0_COMMIT, "--", *restored_paths)
    if comparison.returncode != 0:
        raise ValueError("retired runtime paths differ from the pre-A5e0 source shape")

    forbidden = []
    for path in (root / "crates").rglob("*"):
        if not path.is_file() or "target" in path.parts:
            continue
        relative = path.relative_to(root).as_posix()
        if "a5e0" in relative.lower():
            forbidden.append(relative)
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "a5e0" in text.lower() or "direct_annual_state" in text.lower():
            forbidden.append(relative)
    if forbidden:
        raise ValueError(f"A5e0 production references remain: {sorted(set(forbidden))}")

    metadata_run = run(root, "cargo", "metadata", "--no-deps", "--format-version", "1")
    if metadata_run.returncode != 0:
        raise ValueError("cargo metadata failed: " + metadata_run.stderr)
    metadata = json.loads(metadata_run.stdout)
    target_text = json.dumps(
        [package["targets"] for package in metadata["packages"]], sort_keys=True
    ).lower()
    if "a5e0" in target_text:
        raise ValueError("cargo metadata still exposes an A5e0 target")

    registry = (root / "docs/specifications/README.md").read_text(encoding="utf-8")
    if "runtime retired by A5f1" not in registry:
        raise ValueError("specification registry lacks the A5f1 retirement status")
    package = (
        root
        / "docs/work-packages/20260714-a5f1-retired-a5e0-runtime-cleanup/package.md"
    ).read_text(encoding="utf-8")
    if "Status: `EXECUTED-COMPLETE`" not in package:
        raise ValueError("A5f1 package is not terminal")

    print("A5f1 runtime absence, source restoration, and record preservation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
